# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the behaviours for the APY estimation skill."""
import datetime
import json
import os
from abc import ABC
from typing import Any, Dict, Generator, Optional, Set, Tuple, Type, Union, cast

import numpy as np
import pandas as pd
from aea.helpers.ipfs.base import IPFSHashOnly
from optuna import Study
from pmdarima.pipeline import Pipeline

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.apy_estimation.ml.forecasting import TestReportType
from packages.valory.skills.apy_estimation.ml.io import load_forecaster, save_forecaster
from packages.valory.skills.apy_estimation.ml.preprocessing import prepare_pair_data
from packages.valory.skills.apy_estimation.models import APYParams, SharedState
from packages.valory.skills.apy_estimation.payloads import (
    EstimatePayload,
    FetchingPayload,
    OptimizationPayload,
    PreprocessPayload,
    RegistrationPayload,
    ResetPayload,
    TestingPayload,
    TrainingPayload,
    TransformationPayload,
)
from packages.valory.skills.apy_estimation.rounds import (
    APYEstimationAbciApp,
    CollectHistoryRound,
    EstimateRound,
    OptimizeRound,
    PeriodState,
    PreprocessRound,
    RegistrationRound,
    ResetAndPauseRound,
    ResetRound,
    TestRound,
    TrainRound,
    TransformRound,
)
from packages.valory.skills.apy_estimation.tasks import (
    OptimizeTask,
    TestTask,
    TrainTask,
    TransformTask,
)
from packages.valory.skills.apy_estimation.tools.etl import load_hist
from packages.valory.skills.apy_estimation.tools.general import (
    create_pathdirs,
    gen_unix_timestamps,
    read_json_file,
    to_json_file,
)
from packages.valory.skills.apy_estimation.tools.queries import (
    block_from_timestamp_q,
    eth_price_usd_q,
    pairs_q,
    top_n_pairs_q,
)


benchmark_tool = BenchmarkTool()
PAIR_ID = "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c"


class APYEstimationBaseState(BaseState, ABC):
    """Base state behaviour for the APY estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> APYParams:
        """Return the params."""
        return cast(APYParams, self.context.params)


class TendermintHealthcheckBehaviour(APYEstimationBaseState):
    """Check whether Tendermint nodes are running."""

    state_id = "tendermint_healthcheck"
    matching_round = None

    _check_started: Optional[datetime.datetime] = None
    _timeout: float
    _is_healthy: bool

    def start(self) -> None:
        """Set up the behaviour."""
        if self._check_started is None:
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False

    def _is_timeout_expired(self) -> bool:
        """Check if the timeout expired."""
        expired = False  # pragma: no cover

        if self._check_started is not None and not self._is_healthy:
            expired = (
                datetime.datetime.now()
                > self._check_started + datetime.timedelta(0, self._timeout)
            )

        return expired

    def async_act(self) -> Generator:
        """Do the action."""
        self.start()
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            raise RuntimeError("Tendermint node did not come live!")

        if not self._is_healthy:
            health = yield from self._get_health()
            try:
                json.loads(health.body.decode())

            except json.JSONDecodeError:
                self.context.logger.error("Tendermint not running yet, trying again!")
                yield from self.sleep(self.params.sleep_time)
                return

            self._is_healthy = True

        status = yield from self._get_status()

        try:
            json_body = json.loads(status.body.decode())

        except json.JSONDecodeError:
            self.context.logger.error(
                "Tendermint not accepting transactions yet, trying again!"
            )
            yield from self.sleep(self.params.sleep_time)
            return

        remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
        local_height = self.context.state.period.height
        self.context.logger.info(
            "local-height = %s, remote-height=%s", local_height, remote_height
        )

        if local_height != remote_height:
            self.context.logger.info("local height != remote height; retrying...")
            yield from self.sleep(self.params.sleep_time)
            return

        self.context.logger.info("local height == remote height; done")
        self.set_done()


class RegistrationBehaviour(APYEstimationBaseState):
    """Register to the next periods."""

    state_id = "register"
    matching_round = RegistrationRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            payload = RegistrationPayload(self.context.agent_address)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class EmptyResponseError(Exception):
    """Exception for empty response."""


class FetchBehaviour(APYEstimationBaseState):
    """Observe historical data."""

    state_id = "fetch"
    matching_round = CollectHistoryRound

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._save_path = ""

    def setup(self) -> None:
        """Set the behaviour up."""
        self._save_path = os.path.join(self.params.data_folder, "historical_data.json")
        create_pathdirs(self._save_path)

    def _handle_response(
        self, res: Dict, res_context: str, keys: Tuple[Union[str, int], ...]
    ) -> None:
        """Handle a response from a subgraph.

        :param res: the response to handle.
        :param res_context: the context of the current response.
        """
        if res is None:
            self.context.logger.error(
                f"Could not get {res_context} from {self.context.spooky_subgraph.api_id}"
            )

            self.context.spooky_subgraph.increment_retries()
            yield from self.sleep(self.params.sleep_time)
            raise EmptyResponseError()

        value = res[keys[0]]
        if len(keys) > 1:
            for key in keys[1:]:
                value = value[key]

        self.context.logger.info(f"Retrieved {res_context}: {value}.")
        self.context.spooky_subgraph.reset_retries()

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the historical data until now, for the configured duration.
        - If the request fails, retry until max retries are exceeded.
        - Send an observation transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        if self.context.spooky_subgraph.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.wait_until_round_end()
            self.set_done()

        else:
            with benchmark_tool.measure(
                self,
            ).local():
                # Fetch top n pool ids.
                spooky_api_specs = self.context.spooky_subgraph.get_spec()
                available_specs = set(spooky_api_specs.keys())
                needed_specs = {"method", "url", "headers"}
                unwanted_specs = available_specs - (available_specs & needed_specs)

                for unwanted in unwanted_specs:
                    spooky_api_specs.pop(unwanted)

                res_raw = yield from self.get_http_response(
                    content=top_n_pairs_q(self.context.spooky_subgraph.top_n_pools),
                    **spooky_api_specs,
                )
                res = self.context.spooky_subgraph.process_response(res_raw)

                try:
                    self._handle_response(
                        res,
                        res_context=f"top {self.context.spooky_subgraph.top_n_pools} pool ids (Showing first example)",
                        keys=("pairs", 0, "id"),
                    )
                except EmptyResponseError:
                    return

                pair_ids = [pair["id"] for pair in res["pairs"]]

                pairs_hist = []
                for timestamp in gen_unix_timestamps(self.params.history_duration):

                    # Fetch block.
                    fantom_api_specs = self.context.fantom_subgraph.get_spec()
                    res_raw = yield from self.get_http_response(
                        method=fantom_api_specs["method"],
                        url=fantom_api_specs["url"],
                        headers=fantom_api_specs["headers"],
                        content=block_from_timestamp_q(timestamp),
                    )
                    res = self.context.fantom_subgraph.process_response(res_raw)

                    try:
                        self._handle_response(
                            res, res_context="block", keys=("blocks", 0)
                        )
                    except EmptyResponseError:
                        return

                    fetched_block = res["blocks"][0]

                    # Fetch ETH price for block.
                    res_raw = yield from self.get_http_response(
                        content=eth_price_usd_q(
                            self.context.spooky_subgraph.bundle_id,
                            fetched_block["number"],
                        ),
                        **spooky_api_specs,
                    )
                    res = self.context.spooky_subgraph.process_response(res_raw)

                    try:
                        self._handle_response(
                            res,
                            res_context=f"ETH price for block {fetched_block}",
                            keys=("bundles", 0, "ethPrice"),
                        )
                    except EmptyResponseError:
                        return

                    eth_price = float(res["bundles"][0]["ethPrice"])

                    # Fetch top n pool data for block.
                    res_raw = yield from self.get_http_response(
                        content=pairs_q(fetched_block["number"], pair_ids),
                        **spooky_api_specs,
                    )
                    res = self.context.spooky_subgraph.process_response(res_raw)

                    try:
                        self._handle_response(
                            res,
                            res_context=f"top {self.context.spooky_subgraph.top_n_pools} "
                            f"pool data for block {fetched_block} (Showing first example)",
                            keys=("pairs", 0),
                        )
                    except EmptyResponseError:
                        return

                    # Add extra fields to the pairs.
                    for i in range(len(res["pairs"])):
                        res["pairs"][i]["for_timestamp"] = timestamp
                        res["pairs"][i]["block_number"] = fetched_block["number"]
                        res["pairs"][i]["block_timestamp"] = fetched_block["timestamp"]
                        res["pairs"][i]["eth_price"] = eth_price

                    pairs_hist.extend(res["pairs"])

            if len(pairs_hist) > 0:
                # Store historical data to a json file.
                try:
                    to_json_file(self._save_path, pairs_hist)
                except OSError:
                    self.context.logger.error(f"Path '{self._save_path}' could not be found!")
                except TypeError:
                    self.context.logger.error(f"Historical data cannot be JSON serialized!")

                # Hash the file.
                hasher = IPFSHashOnly()
                hist_hash = hasher.get(self._save_path)

                # Pass the hash as a Payload.
                payload = FetchingPayload(
                    self.context.agent_address,
                    hist_hash,
                )

                # Finish behaviour.
                with benchmark_tool.measure(
                    self,
                ).consensus():
                    yield from self.send_a2a_transaction(payload)
                    yield from self.wait_until_round_end()

                self.set_done()


class TransformBehaviour(APYEstimationBaseState):
    """Transform historical data, i.e., convert them to a dataframe and calculate useful metrics, such as the APY."""

    state_id = "transform"
    matching_round = TransformRound

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._history_save_path = self._transformed_history_save_path = ""
        self._async_result = None

    def setup(self):
        """Setup behaviour."""
        self._history_save_path = os.path.join(
            self.params.data_folder, "historical_data.json"
        )
        self._transformed_history_save_path = os.path.join(
            self.params.data_folder, "transformed_historical_data.csv"
        )
        create_pathdirs(self._transformed_history_save_path)

        # Load historical data from a json file.
        try:
            pairs_hist = read_json_file(self._history_save_path)
        except OSError:
            self.context.logger.error(f"Path '{self._history_save_path}' could not be found!")
        except json.JSONDecodeError:
            self.context.logger.error(f"File '{self._history_save_path}' has an invalid JSON encoding!")
        except ValueError:
            self.context.logger.error(f"There is an encoding error in the '{self._history_save_path}' file!")

        transform_task = TransformTask()
        task_id = self.context.task_manager.enqueue_task(
            transform_task, args=(pairs_hist,)
        )
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result.ready() is False:
            self.context.logger.debug("The transform task is not finished yet.")
            yield from self.sleep(self.params.sleep_time)

        else:
            # Get the transformed data from the task.
            completed_task = self._async_result.get()
            transformed_history = cast(pd.DataFrame, completed_task.result)
            self.context.logger.info(
                "Data have been transformed. Showing the first row:\n",
                transformed_history.head(1),
            )

            # Store the transformed data.
            transformed_history.to_csv(self._transformed_history_save_path)

            # Hash the file.
            hasher = IPFSHashOnly()
            hist_hash = hasher.get(self._transformed_history_save_path)

            # Pass the hash as a Payload.
            payload = TransformationPayload(
                self.context.agent_address,
                hist_hash,
            )

            # Finish behaviour.
            with benchmark_tool.measure(self).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()


class PreprocessBehaviour(APYEstimationBaseState):
    """Preprocess historical data (train-test split)."""

    state_id = "preprocess"
    matching_round = PreprocessRound

    def async_act(self) -> Generator:
        """Do the action."""
        # TODO Currently we run it only for one pool, the USDC-FTM.
        #  Eventually, we will have to run this and all the following behaviours for all the available pools.

        # Get the historical data and preprocess them.
        transformed_history_save_path = os.path.join(
            self.params.data_folder, "transformed_historical_data.csv"
        )
        pairs_hist = load_hist(transformed_history_save_path)
        (y_train, y_test), pair_name = prepare_pair_data(pairs_hist, PAIR_ID)
        self.context.logger.info("Data have been preprocessed.")

        # Store and hash the preprocessed data.
        hasher = IPFSHashOnly()
        hashes = []
        for filename, split in {"train": y_train, "test": y_test}.items():
            save_path = os.path.join(
                self.params.data_folder, PAIR_ID, f"{filename}.csv"
            )
            create_pathdirs(save_path)
            np.savetxt(save_path, split, ",")
            hashes.append(hasher.get(save_path))

        # Pass the hash as a Payload.
        payload = PreprocessPayload(
            self.context.agent_address, hashes[0], hashes[1], pair_name
        )

        # Finish behaviour.
        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class OptimizeBehaviour(APYEstimationBaseState):
    """Run an optimization study based on the training data."""

    state_id = "optimize"
    matching_round = OptimizeRound

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._async_result = None

    def setup(self):
        """Setup behaviour."""
        # Load training data.
        path = os.path.join(self.params.data_folder, PAIR_ID, "train.csv")
        y = np.loadtxt(path, delimiter=",")

        optimize_task = OptimizeTask()
        task_id = self.context.task_manager.enqueue_task(
            optimize_task, args=(y,), kwargs=self.params.optimizer_params
        )
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result.ready() is False:
            self.context.logger.debug("The optimization task is not finished yet.")
            yield from self.sleep(self.params.sleep_time)

        else:
            # Run the optimizer and get the study's result.
            completed_task = self._async_result.get()
            study = cast(Study, completed_task.result)
            study_results = study.trials_dataframe()
            self.context.logger.info(
                "Optimization has finished. Showing the results:\n",
                study_results.to_string(),
            )

            # Store the results.
            save_path = os.path.join(
                self.params.data_folder, PAIR_ID, "study_results.csv"
            )
            study_results.to_csv(save_path)

            # Hash the file.
            hasher = IPFSHashOnly()
            study_hash = hasher.get(save_path)

            # Pass the hash and the best trial as a Payload.
            payload = OptimizationPayload(
                self.context.agent_address, study_hash, study.best_params
            )

            # Finish behaviour.
            with benchmark_tool.measure(self).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()


class TrainBehaviour(APYEstimationBaseState):
    """Train an estimator."""

    state_id = "train"
    matching_round = TrainRound

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._async_result = None

    def setup(self):
        """Setup behaviour."""
        # Load training data.
        if self.period_state.full_training:
            y = []
            for split in ("train", "test"):
                path = os.path.join(self.params.data_folder, PAIR_ID, f"{split}.csv")
                y.append(np.loadtxt(path, delimiter=","))
            y = np.concatenate(y)
        else:
            path = os.path.join(self.params.data_folder, PAIR_ID, "train.csv")
            y = np.loadtxt(path, delimiter=",")

        train_task = TrainTask()
        task_id = self.context.task_manager.enqueue_task(
            train_task, args=(y,), kwargs=self.period_state.best_params
        )
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result.ready() is False:
            self.context.logger.debug("The training task is not finished yet.")
            yield from self.sleep(self.params.sleep_time)

        else:
            # Train the estimator.
            completed_task = self._async_result.get()
            forecaster = cast(Pipeline, completed_task.result)
            self.context.logger.info("Training has finished.")

            # Store the results.
            prefix = "fully_trained_" if self.period_state.full_training else ""
            save_path = os.path.join(
                self.params.data_folder, PAIR_ID, f"{prefix}forecaster.pkl"
            )
            save_forecaster(save_path, forecaster)

            # Hash the file.
            hasher = IPFSHashOnly()
            model_hash = hasher.get(save_path)

            # Pass the hash and the best trial as a Payload.
            payload = TrainingPayload(self.context.agent_address, model_hash)

            # Finish behaviour.
            with benchmark_tool.measure(self).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()


class TestBehaviour(APYEstimationBaseState):
    """Test an estimator."""

    state_id = "test"
    matching_round = TestRound

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._async_result = None

    def setup(self):
        """Setup behaviour."""
        # Load test data.
        y = {"train": None, "y_test": None}
        for split in ("train", "test"):
            path = os.path.join(self.params.data_folder, PAIR_ID, f"{split}.csv")
            y[split] = np.loadtxt(path, delimiter=",")

        model_path = os.path.join(self.params.data_folder, PAIR_ID, f"forecaster.pkl")
        forecaster = load_forecaster(model_path)

        test_task = TestTask()
        task_args = (
            forecaster,
            y["train"],
            y["test"],
            self.period_state.pair_name,
            self.params.testing["steps_forward"],
        )
        task_id = self.context.task_manager.enqueue_task(test_task, task_args)
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result.ready() is False:
            self.context.logger.debug("The testing task is not finished yet.")
            yield from self.sleep(self.params.sleep_time)

        else:
            # Train the estimator.
            completed_task = self._async_result.get()
            report = cast(TestReportType, completed_task.result)
            self.context.logger.info(
                f"Testing has finished. Report follows:\n{json.dumps(report)}"
            )

            # Store the results.
            save_path = os.path.join(
                self.params.data_folder, PAIR_ID, f"test_report.json"
            )
            try:
                to_json_file(save_path, report)
            except OSError:
                self.context.logger.error(f"Path '{save_path}' could not be found!")
            except TypeError:
                self.context.logger.error(f"Report cannot be JSON serialized!")

            # Hash the file.
            hasher = IPFSHashOnly()
            report_hash = hasher.get(save_path)

            # Pass the hash and the best trial as a Payload.
            payload = TestingPayload(self.context.agent_address, report_hash)

            # Finish behaviour.
            with benchmark_tool.measure(self).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()


class EstimateBehaviour(APYEstimationBaseState):
    """Estimate APY."""

    state_id = "estimate"
    matching_round = EstimateRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Run the script to compute the estimate starting from the shared observations.
        - Build an estimate transaction and send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        with benchmark_tool.measure(self).local():
            model_path = os.path.join(
                self.params.data_folder, PAIR_ID, f"fully_trained_forecaster.pkl"
            )
            forecaster = load_forecaster(model_path)
            estimation = forecaster.predict(self.params.estimation["steps_forward"])

            self.context.logger.info(
                "Got estimate of APY for %s: %s",
                self.period_state.pair_name,
                estimation,
            )

            payload = EstimatePayload(self.context.agent_address, estimation)

        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class BaseResetBehaviour(APYEstimationBaseState):
    """Reset state."""

    pause = True

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Trivially log the state.
        - Sleep for configured interval.
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        if self.pause:

            if self.period_state.is_most_voted_estimate_set:
                self.context.logger.info(
                    f"Finalized estimate: {self.period_state.most_voted_estimate}"
                )

            else:
                self.context.logger.info("Finalized estimate not available.")

            self.context.logger.info("Period end.")
            benchmark_tool.save()

            yield from self.wait_from_last_timestamp(self.params.observation_interval)

        else:
            self.context.logger.info(
                f"Period {self.period_state.period_count} was not finished. Resetting!"
            )

        payload = ResetPayload(
            self.context.agent_address, self.period_state.period_count + 1
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class ResetBehaviour(BaseResetBehaviour):
    """Reset state."""

    matching_round = ResetRound
    state_id = "reset"
    pause = False


class ResetAndPauseBehaviour(BaseResetBehaviour):
    """Reset state."""

    matching_round = ResetAndPauseRound
    state_id = "reset_and_pause"


class APYEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the APY estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = APYEstimationAbciApp
    behaviour_states: Set[Type[APYEstimationBaseState]] = {
        TendermintHealthcheckBehaviour,
        RegistrationBehaviour,
        FetchBehaviour,
        TransformBehaviour,
        PreprocessBehaviour,
        OptimizeBehaviour,
        TrainBehaviour,
        TestBehaviour,
        EstimateBehaviour,
        ResetBehaviour,
        ResetAndPauseBehaviour,
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
