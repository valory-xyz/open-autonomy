# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import calendar
import os
from abc import ABC
from multiprocessing.pool import AsyncResult
from typing import (
    Any,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import numpy as np
import pandas as pd
from optuna import Study
from pmdarima.pipeline import Pipeline

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.io.load import SupportedFiletype
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool, VerifyDrand
from packages.valory.skills.apy_estimation_abci.composition import (
    APYEstimationAbciAppChained,
)
from packages.valory.skills.apy_estimation_abci.ml.forecasting import TestReportType
from packages.valory.skills.apy_estimation_abci.ml.preprocessing import (
    prepare_pair_data,
)
from packages.valory.skills.apy_estimation_abci.models import APYParams, SharedState
from packages.valory.skills.apy_estimation_abci.payloads import (
    BatchPreparationPayload,
    EstimatePayload,
    FetchingPayload,
    OptimizationPayload,
    PreprocessPayload,
    RandomnessPayload,
    ResetPayload,
    TestingPayload,
    TrainingPayload,
    TransformationPayload,
    UpdatePayload,
)
from packages.valory.skills.apy_estimation_abci.rounds import (
    APYEstimationAbciApp,
    CollectHistoryRound,
    CollectLatestHistoryBatchRound,
    CycleResetRound,
    EstimateRound,
    FreshModelResetRound,
    OptimizeRound,
    PeriodState,
    PrepareBatchRound,
    PreprocessRound,
    RandomnessRound,
    TestRound,
    TrainRound,
    TransformRound,
    UpdateForecasterRound,
)
from packages.valory.skills.apy_estimation_abci.tasks import (
    OptimizeTask,
    TestTask,
    TrainTask,
    TransformTask,
)
from packages.valory.skills.apy_estimation_abci.tools.etl import (
    ResponseItemType,
    revert_transform_hist_data,
    transform_hist_data,
)
from packages.valory.skills.apy_estimation_abci.tools.general import gen_unix_timestamps
from packages.valory.skills.apy_estimation_abci.tools.io import load_hist
from packages.valory.skills.apy_estimation_abci.tools.queries import (
    block_from_timestamp_q,
    eth_price_usd_q,
    latest_block,
    pairs_q,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    TendermintHealthcheckBehaviour,
)


benchmark_tool = BenchmarkTool()


class APYEstimationBaseState(BaseState, ABC):
    """Base state behaviour for the APY estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> APYParams:
        """Return the params."""
        return cast(APYParams, self.context.params)


class FetchBehaviour(APYEstimationBaseState):
    """Observe historical data."""

    state_id = "fetch"
    matching_round = CollectHistoryRound
    batch = False

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._last_timestamp_unix: Optional[int] = None
        self._save_path = ""
        self._spooky_api_specs: Dict[str, Any] = dict()
        self._timestamps_iterator: Optional[Iterator[int]] = None
        self._current_timestamp: Optional[int] = None
        self._call_failed = False
        self._pairs_hist: ResponseItemType = []
        self._hist_hash: Optional[str] = None

    def setup(self) -> None:
        """Set the behaviour up."""
        last_timestamp = cast(
            SharedState, self.context.state
        ).period.abci_app.last_timestamp
        self._last_timestamp_unix = int(calendar.timegm(last_timestamp.timetuple()))
        filename = "historical_data"

        if self.batch:
            filename += f"_batch_{self._last_timestamp_unix}"
            self._timestamps_iterator = iter((self._last_timestamp_unix,))
        else:
            self._timestamps_iterator = gen_unix_timestamps(
                self._last_timestamp_unix, self.params.history_duration
            )

        self._save_path = os.path.join(
            self.context.data_dir,
            f"{filename}.json",
        )

        self._spooky_api_specs = self.context.spooky_subgraph.get_spec()
        available_specs = set(self._spooky_api_specs.keys())
        needed_specs = {"method", "url", "headers"}
        unwanted_specs = available_specs - (available_specs & needed_specs)

        for unwanted in unwanted_specs:
            self._spooky_api_specs.pop(unwanted)

    def _set_current_timestamp(self) -> None:
        """Set the timestamp for the current timestep in the async act."""
        if not self._call_failed:
            self._current_timestamp = next(
                cast(Iterator[int], self._timestamps_iterator),
                None,
            )

        if self.context.spooky_subgraph.is_retries_exceeded():
            # We cannot continue if the data were not fetched.
            # It is going to make the agent fail in the next behaviour while looking for the historical data file.
            self.context.logger.error(
                "Retries were exceeded while downloading the historical data!"
            )
            # This will result in using only the part of the data downloaded so far.
            self._current_timestamp = None

        # if none of the above (call failed and we can retry), the current timestamp will remain the same.

    def _handle_response(
        self,
        res: Optional[Dict],
        res_context: str,
        keys: Tuple[Union[str, int], ...],
        subgraph: ApiSpecs,
    ) -> Generator[None, None, Optional[Any]]:
        """Handle a response from a subgraph.

        :param res: the response to handle.
        :param res_context: the context of the current response.
        :param keys: keys to get the information from the response.
        :param subgraph: api specs.
        :return: the response's result, using the given keys. `None` if response is `None` (has failed).
        :yield: None
        """
        if res is None:
            self.context.logger.error(
                f"Could not get {res_context} from {subgraph.api_id}"
            )

            self._call_failed = True
            subgraph.increment_retries()
            yield from self.sleep(self.params.sleep_time)
            return None

        value = res[keys[0]]
        if len(keys) > 1:
            for key in keys[1:]:
                value = value[key]

        self.context.logger.info(f"Retrieved {res_context}: {value}.")
        self._call_failed = False
        subgraph.reset_retries()
        return value

    def _fetch_batch(self) -> Generator[None, None, None]:
        """Fetch a single batch of the historical data."""
        # Fetch block.
        fantom_api_specs = self.context.fantom_subgraph.get_spec()
        query = (
            latest_block()
            if self.batch
            else block_from_timestamp_q(cast(int, self._current_timestamp))
        )
        res_raw = yield from self.get_http_response(
            method=fantom_api_specs["method"],
            url=fantom_api_specs["url"],
            headers=fantom_api_specs["headers"],
            content=query,
        )
        res = self.context.fantom_subgraph.process_response(res_raw)

        fetched_block = yield from self._handle_response(
            res,
            res_context="block",
            keys=("blocks", 0),
            subgraph=self.context.fantom_subgraph,
        )

        if fetched_block is None:
            return

        # Fetch ETH price for block.
        res_raw = yield from self.get_http_response(
            content=eth_price_usd_q(
                self.context.spooky_subgraph.bundle_id,
                fetched_block["number"],
            ),
            **self._spooky_api_specs,
        )
        res = self.context.spooky_subgraph.process_response(res_raw)

        eth_price = yield from self._handle_response(
            res,
            res_context=f"ETH price for block {fetched_block}",
            keys=("bundles", 0, "ethPrice"),
            subgraph=self.context.spooky_subgraph,
        )

        if eth_price is None:
            return

        # Fetch pool data for block.
        res_raw = yield from self.get_http_response(
            content=pairs_q(fetched_block["number"], self.params.pair_ids),
            **self._spooky_api_specs,
        )
        res = self.context.spooky_subgraph.process_response(res_raw)

        pairs = yield from self._handle_response(
            res,
            res_context=f"pool data for block {fetched_block}",
            keys=("pairs",),
            subgraph=self.context.spooky_subgraph,
        )

        if pairs is None:
            return

        # Add extra fields to the pairs.
        for i in range(len(pairs)):  # pylint: disable=C0200
            pairs[i]["forTimestamp"] = self._current_timestamp
            pairs[i]["blockNumber"] = fetched_block["number"]
            pairs[i]["blockTimestamp"] = fetched_block["timestamp"]
            pairs[i]["ethPrice"] = eth_price

        self._pairs_hist.extend(pairs)

        if not self.batch:
            self.context.logger.info(
                f"Fetched day {len(self._pairs_hist)}/{self.params.history_duration * 30}."
            )

    def async_act(  # pylint: disable=too-many-locals,too-many-statements
        self,
    ) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the historical data until now, for the configured duration.
        - If the request fails, retry until max retries are exceeded.
        - Send an observation transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        self._set_current_timestamp()

        with benchmark_tool.measure(
            self,
        ).local():
            if self._current_timestamp is not None:
                yield from self._fetch_batch()
                return

            if len(self._pairs_hist) == 0:
                self.context.logger.error("Could not download any historical data!")
                self._hist_hash = ""

            if (
                len(self._pairs_hist) > 0
                and len(self._pairs_hist) != self.params.history_duration * 30
                and not self.batch
            ):
                # Here, we continue without having all the pairs downloaded, because of a network issue.
                self.context.logger.warning(
                    "Will continue with partially downloaded historical data!"
                )

            if len(self._pairs_hist) > 0:
                # Send the file to IPFS and get its hash.
                self._hist_hash = self.send_to_ipfs(
                    self._save_path, self._pairs_hist, SupportedFiletype.JSON
                )

            # Pass the hash as a Payload.
            payload = FetchingPayload(
                self.context.agent_address,
                self._hist_hash,
                cast(int, self._last_timestamp_unix),
            )

            # Finish behaviour.
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.spooky_subgraph.reset_retries()
        self.context.fantom_subgraph.reset_retries()


class FetchBatchBehaviour(FetchBehaviour):
    """Observe the latest batch of historical data."""

    state_id = "fetch_batch"
    matching_round = CollectLatestHistoryBatchRound
    batch = True


class TransformBehaviour(APYEstimationBaseState):
    """Transform historical data, i.e., convert them to a dataframe and calculate useful metrics, such as the APY."""

    state_id = "transform"
    matching_round = TransformRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._transformed_history_save_path = ""
        self._async_result: Optional[AsyncResult] = None
        self._pairs_hist: Optional[ResponseItemType] = None
        self._transformed_hist_hash: Optional[str] = None
        self._latest_observation_hist_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        self._pairs_hist = self.get_from_ipfs(
            self.period_state.history_hash,
            self.context.data_dir,
            "historical_data.json",
            SupportedFiletype.JSON,
        )

        self._transformed_history_save_path = os.path.join(
            self.context.data_dir,
            "transformed_historical_data.csv",
        )

        if self._pairs_hist is not None:
            transform_task = TransformTask()
            task_id = self.context.task_manager.enqueue_task(
                transform_task, args=(self._pairs_hist,)
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._pairs_hist is not None:
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The transform task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the transformed data from the task.
            completed_task = self._async_result.get()
            transformed_history = cast(pd.DataFrame, completed_task)
            self.context.logger.info(
                f"Data have been transformed:\n{transformed_history.to_string()}"
            )

            # Send the transformed history to IPFS and get its hash.
            self._transformed_hist_hash = self.send_to_ipfs(
                self._transformed_history_save_path,
                transformed_history,
                SupportedFiletype.CSV,
            )

            # Get the latest observation.
            latest_observation = transformed_history.iloc[[-1]]
            # Send the latest observation to IPFS and get its hash.
            latest_observation_save_path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
                "latest_observation.csv",
            )
            self._latest_observation_hist_hash = self.send_to_ipfs(
                latest_observation_save_path,
                latest_observation,
                SupportedFiletype.CSV,
                index=True,
            )

        # Pass the hash as a Payload.
        payload = TransformationPayload(
            self.context.agent_address,
            self._transformed_hist_hash,
            self._latest_observation_hist_hash,
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
        pairs_hist = self.get_from_ipfs(
            self.period_state.transformed_history_hash,
            self.context.data_dir,
            "transformed_historical_data.csv",
            custom_loader=load_hist,
        )

        hashes = [None] * 2
        pair_name = ""

        if pairs_hist is not None:
            (y_train, y_test), pair_name = prepare_pair_data(
                pairs_hist, self.params.pair_ids[0]
            )
            self.context.logger.info("Data have been preprocessed.")
            self.context.logger.info(f"y_train: {y_train.to_string()}")
            self.context.logger.info(f"y_test: {y_test.to_string()}")

            # Store and hash the preprocessed data.
            for i, (filename, split) in enumerate(
                {"train": y_train, "test": y_test}.items()
            ):
                save_path = os.path.join(
                    self.context.data_dir,
                    self.params.pair_ids[0],
                    f"y_{filename}.csv",
                )
                split_hash = self.send_to_ipfs(save_path, split, SupportedFiletype.CSV)
                hashes[i] = split_hash

        # Pass the hash as a Payload.
        payload = PreprocessPayload(
            self.context.agent_address, pair_name, hashes[0], hashes[1]
        )

        # Finish behaviour.
        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PrepareBatchBehaviour(APYEstimationBaseState):
    """Transform and preprocess batch data."""

    state_id = "prepare_batch"
    matching_round = PrepareBatchRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._batch: Optional[ResponseItemType] = None
        self._prepared_batch_save_path = ""
        self._previous_batch: Optional[pd.DataFrame] = None
        self._prepared_batch_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        path_to_pair = os.path.join(
            self.context.data_dir,
            self.params.pair_ids[0],
        )

        batch_path_args = path_to_pair, "latest_observation.csv"
        self._prepared_batch_save_path = os.path.join(*batch_path_args)

        self._previous_batch = self.get_from_ipfs(
            self.period_state.latest_observation_hist_hash,
            *batch_path_args,
            custom_loader=load_hist,
        )

        self._batch = self.get_from_ipfs(
            self.period_state.batch_hash,
            self.context.data_dir,
            f"historical_data_batch_{self.period_state.latest_observation_timestamp}.json",
            SupportedFiletype.JSON,
        )

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(batch is None for batch in (self._previous_batch, self._batch)):
            # Revert transformation on the previous batch.
            previous_batch = revert_transform_hist_data(
                cast(pd.DataFrame, self._previous_batch)
            )[0]
            # Insert the latest batch as a row before transforming, in order to be able to calculate the APY.
            cast(ResponseItemType, self._batch).insert(0, previous_batch)

            # Transform and filter data.
            # We are not using a `Task` here, because preparing a single batch is not intense.
            self.context.logger.info(f"Batch is:\n{self._batch}")
            transformed_batch = transform_hist_data(cast(ResponseItemType, self._batch))
            self.context.logger.info(
                f"Batch has been transformed:\n{transformed_batch.to_string()}"
            )

            # Send the file to IPFS and get its hash.
            self._prepared_batch_hash = self.send_to_ipfs(
                self._prepared_batch_save_path, transformed_batch, SupportedFiletype.CSV
            )

        # Pass the hash as a Payload.
        payload = BatchPreparationPayload(
            self.context.agent_address,
            self._prepared_batch_hash,
        )

        # Finish behaviour.
        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RandomnessBehaviour(APYEstimationBaseState):
    """Get randomness value from `drnand`."""

    state_id = "randomness"
    matching_round = RandomnessRound

    def async_act(self) -> Generator:
        """Get randomness value from `drnand`."""
        if self.context.randomness_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with benchmark_tool.measure(
            self,
        ).local():
            api_specs = self.context.randomness_api.get_spec()
            response = yield from self.get_http_response(
                method=api_specs["method"],
                url=api_specs["url"],
            )
            observation = self.context.randomness_api.process_response(response)

        if not observation:
            self.context.logger.error(
                f"Could not get randomness from {self.context.randomness_api.api_id}"
            )
            yield from self.sleep(self.params.sleep_time)
            self.context.randomness_api.increment_retries()
            return

        self.context.logger.info(f"Retrieved DRAND values: {observation}.")
        self.context.logger.info("Verifying DRAND values.")
        drand_check = VerifyDrand()
        check, error = drand_check.verify(observation, self.params.drand_public_key)

        if check:
            self.context.logger.info("DRAND check successful.")
        else:
            self.context.logger.info(f"DRAND check failed, {error}.")
            observation["randomness"] = ""
            observation["round"] = ""

        payload = RandomnessPayload(
            self.context.agent_address,
            observation["round"],
            observation["randomness"],
        )
        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.randomness_api.reset_retries()


class OptimizeBehaviour(APYEstimationBaseState):
    """Run an optimization study based on the training data."""

    state_id = "optimize"
    matching_round = OptimizeRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._y: Optional[pd.DataFrame] = None
        self._best_params_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load training data.
        training_data_path = os.path.join(
            self.context.data_dir,
            self.params.pair_ids[0],
        )
        self._y = self.get_from_ipfs(
            self.period_state.train_hash,
            training_data_path,
            "y_train.csv",
            SupportedFiletype.CSV,
        )

        if self._y is not None:
            optimize_task = OptimizeTask()
            task_id = self.context.task_manager.enqueue_task(
                optimize_task,
                args=(
                    self._y.values.ravel(),
                    self.period_state.most_voted_randomness,
                ),
                kwargs=self.params.optimizer_params,
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._y is not None:
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The optimization task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the study's result.
            completed_task = self._async_result.get()
            study = cast(Study, completed_task)
            study_results = study.trials_dataframe()
            self.context.logger.info(
                "Optimization has finished. Showing the results:\n"
                f"{study_results.to_string()}"
            )

            # Store the best params from the results.
            best_params_save_path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
                "best_params.json",
            )

            try:
                best_params = study.best_params

            except ValueError:
                # If no trial finished, set random params as best.
                best_params = study.trials[0].params
                self.context.logger.warning(
                    "The optimization could not be done! "
                    "Please make sure that there is a sufficient number of data "
                    "for the optimization procedure. Setting best parameters randomly!"
                )
                # Fix: exit round via fail event and move to right round

            self._best_params_hash = self.send_to_ipfs(
                best_params_save_path, best_params, SupportedFiletype.JSON
            )

        # Pass the best params hash as a Payload.
        payload = OptimizationPayload(
            self.context.agent_address, self._best_params_hash
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

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._best_params: Optional[Dict[str, Any]] = None
        self._y: Optional[np.ndarray] = None
        self._model_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load the best params from the optimization results.
        best_params_path = os.path.join(
            self.context.data_dir,
            self.params.pair_ids[0],
        )
        self._best_params = self.get_from_ipfs(
            self.period_state.params_hash,
            best_params_path,
            "best_params.json",
            SupportedFiletype.JSON,
        )

        # Load training data.
        splits: Optional[List[np.ndarray]] = []
        if self.period_state.full_training:
            for split in ("train", "test"):
                path = os.path.join(
                    self.context.data_dir,
                    self.params.pair_ids[0],
                )
                df = self.get_from_ipfs(
                    getattr(self.period_state, f"{split}_hash"),
                    path,
                    f"y_{split}.csv",
                    SupportedFiletype.CSV,
                )
                if df is None:
                    splits = None
                    break
                cast(List[np.ndarray], splits).append(df.values.ravel())

            if splits is not None:
                self._y = np.concatenate(splits)

        else:
            path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
            )
            df = self.get_from_ipfs(
                self.period_state.train_hash, path, "y_train.csv", SupportedFiletype.CSV
            )
            if df is not None:
                self._y = df.values.ravel()

        if not any(arg is None for arg in (self._y, self._best_params)):
            train_task = TrainTask()
            task_id = self.context.task_manager.enqueue_task(
                train_task, args=(self._y,), kwargs=self._best_params
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(arg is None for arg in (self._y, self._best_params)):
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The training task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the trained estimator.
            completed_task = self._async_result.get()
            forecaster = cast(Pipeline, completed_task)
            self.context.logger.info("Training has finished.")

            prefix = "fully_trained_" if self.period_state.full_training else ""
            forecaster_save_path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
                f"{prefix}forecaster.joblib",
            )

            # Send the file to IPFS and get its hash.
            self._model_hash = self.send_to_ipfs(
                forecaster_save_path, forecaster, SupportedFiletype.PM_PIPELINE
            )

        payload = TrainingPayload(self.context.agent_address, self._model_hash)

        # Finish behaviour.
        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class TestBehaviour(APYEstimationBaseState):
    """Test an estimator."""

    state_id = "test"
    matching_round = TestRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._y_train: Optional[np.ndarray] = None
        self._y_test: Optional[np.ndarray] = None
        self._forecaster: Optional[Pipeline] = None
        self._report_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load data.
        for split in ("train", "test"):
            path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
            )
            df = self.get_from_ipfs(
                getattr(self.period_state, f"{split}_hash"),
                path,
                f"y_{split}.csv",
                SupportedFiletype.CSV,
            )
            if df is not None:
                setattr(self, f"_y_{split}", df.values.ravel())

        model_path = os.path.join(
            self.context.data_dir,
            self.params.pair_ids[0],
        )

        self._forecaster = self.get_from_ipfs(
            self.period_state.model_hash,
            model_path,
            "forecaster.joblib",
            SupportedFiletype.PM_PIPELINE,
        )

        if not any(
            arg is None for arg in (self._y_train, self._y_test, self._forecaster)
        ):
            test_task = TestTask()
            task_args = (
                self._forecaster,
                self._y_train,
                self._y_test,
                self.period_state.pair_name,
                self.params.testing["steps_forward"],
            )
            task_id = self.context.task_manager.enqueue_task(test_task, task_args)
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(
            arg is None for arg in (self._y_train, self._y_test, self._forecaster)
        ):
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The testing task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the test report.
            completed_task = self._async_result.get()
            report = cast(TestReportType, completed_task)
            self.context.logger.info(f"Testing has finished. Report follows:\n{report}")

            # Store the results.
            report_save_path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
                "test_report.json",
            )
            # Send the file to IPFS and get its hash.
            self._report_hash = self.send_to_ipfs(
                report_save_path, report, SupportedFiletype.JSON
            )

        # Pass the hash and the best trial as a Payload.
        payload = TestingPayload(self.context.agent_address, self._report_hash)

        # Finish behaviour.
        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class UpdateForecasterBehaviour(APYEstimationBaseState):
    """Update an estimator."""

    state_id = "update"
    matching_round = UpdateForecasterRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._y: Optional[np.ndarray] = None
        self._forecaster_filename: Optional[str] = None
        self._forecaster: Optional[Pipeline] = None
        self._model_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        self._forecaster_filename = "fully_trained_forecaster.joblib"
        pair_path = os.path.join(
            self.context.data_dir,
            self.params.pair_ids[0],
        )

        # Load data batch.
        transformed_batch = self.get_from_ipfs(
            self.period_state.latest_observation_hist_hash,
            pair_path,
            "latest_observation.csv",
            SupportedFiletype.CSV,
        )

        if transformed_batch is not None:
            self._y = transformed_batch["APY"].values.ravel()

        # Load forecaster.
        self._forecaster = self.get_from_ipfs(
            self.period_state.model_hash,
            pair_path,
            self._forecaster_filename,
            SupportedFiletype.PM_PIPELINE,
        )

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(arg is None for arg in (self._y, self._forecaster)):
            cast(Pipeline, self._forecaster).update(self._y)
            self.context.logger.info("Forecaster has been updated.")

            # Send the file to IPFS and get its hash.
            forecaster_save_path = os.path.join(
                self.context.data_dir,
                self.params.pair_ids[0],
                cast(str, self._forecaster_filename),
            )
            self._model_hash = self.send_to_ipfs(
                forecaster_save_path, self._forecaster, SupportedFiletype.PM_PIPELINE
            )

        payload = UpdatePayload(self.context.agent_address, self._model_hash)

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
        model_path = os.path.join(
            self.context.data_dir,
            self.params.pair_ids[0],
        )
        forecaster = self.get_from_ipfs(
            self.period_state.model_hash,
            model_path,
            "fully_trained_forecaster.joblib",
            SupportedFiletype.PM_PIPELINE,
        )

        estimation = None
        if forecaster is not None:
            # currently, a `steps_forward != 1` will fail
            estimation = forecaster.predict(self.params.estimation["steps_forward"])[0]

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
        if (
            self.state_id == "cycle_reset"
            and self.period_state.is_most_voted_estimate_set
        ):
            self.context.logger.info(
                f"Finalized estimate: {self.period_state.most_voted_estimate}. Resetting and pausing!"
            )
            self.context.logger.info(
                f"Estimation will happen again in {self.params.observation_interval} seconds."
            )
            yield from self.sleep(self.params.observation_interval)
            benchmark_tool.save()
        elif (
            self.state_id == "cycle_reset"
            and not self.period_state.is_most_voted_estimate_set
        ):
            self.context.logger.info("Finalized estimate not available. Resetting!")
        elif self.state_id == "fresh_model_reset":
            self.context.logger.info("Resetting to create a fresh forecasting model!")
        else:  # pragma: nocover
            raise RuntimeError(
                f"BaseResetBehaviour not used correctly. Got {self.state_id}. "
                f"Allowed state ids are `cycle_reset` and `fresh_model_reset`."
            )

        payload = ResetPayload(
            self.context.agent_address, self.period_state.period_count + 1
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class FreshModelResetBehaviour(BaseResetBehaviour):
    """Reset state to start with a fresh model."""

    matching_round = FreshModelResetRound
    state_id = "fresh_model_reset"


class CycleResetBehaviour(BaseResetBehaviour):
    """Cycle reset state."""

    matching_round = CycleResetRound
    state_id = "cycle_reset"


class EstimatorRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the APY estimation behaviour."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = APYEstimationAbciApp
    behaviour_states: Set[Type[BaseState]] = {
        TendermintHealthcheckBehaviour,  # type: ignore
        FetchBehaviour,
        FetchBatchBehaviour,
        TransformBehaviour,
        PreprocessBehaviour,  # type: ignore
        PrepareBatchBehaviour,
        RandomnessBehaviour,  # type: ignore
        OptimizeBehaviour,
        TrainBehaviour,
        TestBehaviour,
        UpdateForecasterBehaviour,
        EstimateBehaviour,  # type: ignore
        FreshModelResetBehaviour,  # type: ignore
        CycleResetBehaviour,  # type: ignore
    }


class APYEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the APY estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = APYEstimationAbciAppChained

    behaviour_states: Set[Type[BaseState]] = {
        *AgentRegistrationRoundBehaviour.behaviour_states,
        *EstimatorRoundBehaviour.behaviour_states,
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
