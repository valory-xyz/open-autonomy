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
import calendar
import datetime
import json
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
from aea_cli_ipfs.ipfs_utils import IPFSTool
from optuna import Study
from pmdarima.pipeline import Pipeline

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool, VerifyDrand
from packages.valory.skills.apy_estimation_abci.ml.forecasting import TestReportType
from packages.valory.skills.apy_estimation_abci.ml.io import (
    load_forecaster,
    save_forecaster,
)
from packages.valory.skills.apy_estimation_abci.ml.preprocessing import (
    prepare_pair_data,
)
from packages.valory.skills.apy_estimation_abci.models import APYParams, SharedState
from packages.valory.skills.apy_estimation_abci.payloads import (
    EstimatePayload,
    FetchingPayload,
    OptimizationPayload,
    PreprocessPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    TestingPayload,
    TrainingPayload,
    TransformationPayload,
)
from packages.valory.skills.apy_estimation_abci.rounds import (
    APYEstimationAbciApp,
    CollectHistoryRound,
    CycleResetRound,
    EstimateRound,
    OptimizeRound,
    PeriodState,
    PreprocessRound,
    RandomnessRound,
    RegistrationRound,
    ResetRound,
    TestRound,
    TrainRound,
    TransformRound,
)
from packages.valory.skills.apy_estimation_abci.tasks import (
    OptimizeTask,
    TestTask,
    TrainTask,
    TransformTask,
)
from packages.valory.skills.apy_estimation_abci.tools.etl import (
    ResponseItemType,
    load_hist,
)
from packages.valory.skills.apy_estimation_abci.tools.general import (
    HyperParamsType,
    create_pathdirs,
    gen_unix_timestamps,
    read_json_file,
    to_json_file,
)
from packages.valory.skills.apy_estimation_abci.tools.queries import (
    block_from_timestamp_q,
    eth_price_usd_q,
    pairs_q,
)


benchmark_tool = BenchmarkTool()


class APYEstimationBaseState(BaseState, ABC):
    """Base state behaviour for the APY estimation skill."""

    def __init__(self, **kwargs: Any):
        """Initialize an `APYEstimationBaseState` behaviour."""
        super().__init__(**kwargs)
        # Create an IPFS tool.
        self.__ipfs_tool = IPFSTool({"addr": self.params.ipfs_domain_name})
        # Check IPFS node.
        self.__ipfs_tool.check_ipfs_node_running()

    def send_file_to_ipfs_node(self, filepath: str) -> str:
        """Send a file to the IPFS node.

        :param filepath: the filepath of the file to send
        :return: the file's hash
        """
        _, hist_hash, _ = self.__ipfs_tool.add(filepath)

        return hist_hash

    def _download_from_ipfs_node(
        self,
        hash_: str,
        target_dir: str,
        filename: str,
    ) -> str:
        """Download a file from the IPFS node.

        :param hash_: hash of file to download
        :param target_dir: directory to place downloaded file
        :param filename: the original name of the file to download
        :return: the filepath of the downloaded file
        """
        filepath = os.path.join(target_dir, filename)

        if os.path.exists(filepath):  # pragma: nocover
            os.remove(filepath)

        self.__ipfs_tool.download(hash_, target_dir)

        return filepath

    def get_and_read_json(
        self,
        hash_: str,
        target_dir: str,
        filename: str,
    ) -> Union[ResponseItemType, HyperParamsType]:
        """Download a json file from the IPFS node.

        :param hash_: hash of file to download
        :param target_dir: directory to place downloaded file
        :param filename: the original name of the file to download
        :return: the deserialized json file's content
        """
        filepath = self._download_from_ipfs_node(hash_, target_dir, filename)

        try:
            # Load & return data from json file.
            return read_json_file(filepath)

        except OSError as e:  # pragma: nocover
            self.context.logger.error(f"Path '{filepath}' could not be found!")
            raise e

        except json.JSONDecodeError as e:  # pragma: nocover
            self.context.logger.error(
                f"File '{filepath}' has an invalid JSON encoding!"
            )
            raise e

        except ValueError as e:  # pragma: nocover
            self.context.logger.error(
                f"There is an encoding error in the '{filepath}' file!"
            )
            raise e

    def get_and_read_hist(
        self, hash_: str, target_dir: str, filename: str
    ) -> pd.DataFrame:
        """Download a csv file with historical data from the IPFS node.

        :param hash_: hash of file to download
        :param target_dir: directory to place downloaded file
        :param filename: the original name of the file to download
        :return: a pandas dataframe of the downloaded csv
        """
        filepath = self._download_from_ipfs_node(hash_, target_dir, filename)

        try:
            return load_hist(filepath)

        except FileNotFoundError as e:  # pragma: nocover
            self.context.logger.error(f"File {filepath} was not found!")
            raise e

    def get_and_read_csv(
        self, hash_: str, target_dir: str, filename: str
    ) -> pd.DataFrame:
        """Download a csv file from the IPFS node.

        :param hash_: hash of file to download
        :param target_dir: directory to place downloaded file
        :param filename: the original name of the file to download
        :return: a pandas dataframe of the downloaded csv
        """
        filepath = self._download_from_ipfs_node(hash_, target_dir, filename)

        try:
            return pd.read_csv(filepath)

        except FileNotFoundError as e:  # pragma: nocover
            self.context.logger.error(f"File {filepath} was not found!")
            raise e

    def get_and_read_forecaster(
        self, hash_: str, target_dir: str, filename: str
    ) -> Pipeline:
        """Download a csv file from the IPFS node.

        :param hash_: hash of file to download
        :param target_dir: directory to place downloaded file
        :param filename: the original name of the file to download
        :return: a pandas dataframe of the downloaded csv
        """
        filepath = self._download_from_ipfs_node(hash_, target_dir, filename)

        try:
            return load_forecaster(filepath)

        except (NotADirectoryError, FileNotFoundError) as e:  # pragma: nocover
            self.context.logger.error(f"Could not detect {filepath}!")
            raise e

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
        if self._check_started is None or self._is_healthy:
            return False  # pragma: no cover
        return datetime.datetime.now() > self._check_started + datetime.timedelta(
            0, self._timeout
        )

    def async_act(self) -> Generator:
        """Do the action."""

        self.start()
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            raise RuntimeError("Tendermint node did not come live!")
        if not self._is_healthy:
            health = yield from self._get_health()
            try:
                json_body = json.loads(health.body.decode())
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

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._save_path = ""
        self._spooky_api_specs: Dict[str, Any] = dict()
        self._timestamps_iterator: Optional[Iterator[int]] = None
        self._current_timestamp: Optional[int] = None
        self._call_failed = False
        self._pairs_hist: ResponseItemType = []

    def setup(self) -> None:
        """Set the behaviour up."""
        self._save_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            "historical_data.json",
        )
        create_pathdirs(self._save_path)

        self._spooky_api_specs = self.context.spooky_subgraph.get_spec()
        available_specs = set(self._spooky_api_specs.keys())
        needed_specs = {"method", "url", "headers"}
        unwanted_specs = available_specs - (available_specs & needed_specs)

        for unwanted in unwanted_specs:
            self._spooky_api_specs.pop(unwanted)

        last_timestamp = cast(
            SharedState, self.context.state
        ).period.abci_app.last_timestamp
        last_timestamp_unix = int(calendar.timegm(last_timestamp.timetuple()))
        self._timestamps_iterator = gen_unix_timestamps(
            last_timestamp_unix, self.params.history_duration
        )

    def _handle_response(
        self,
        res: Optional[Dict],
        res_context: str,
        keys: Tuple[Union[str, int], ...],
        subgraph: ApiSpecs,
    ) -> None:
        """Handle a response from a subgraph.

        :param res: the response to handle.
        :param res_context: the context of the current response.
        :param keys: keys to get the information from the response.
        :param subgraph: api specs.
        """
        if res is None:
            self.context.logger.error(
                f"Could not get {res_context} from {subgraph.api_id}"
            )

            self._call_failed = True
            subgraph.increment_retries()
            raise EmptyResponseError()

        value = res[keys[0]]
        if len(keys) > 1:
            for key in keys[1:]:
                value = value[key]

        self.context.logger.info(f"Retrieved {res_context}: {value}.")
        self._call_failed = False
        subgraph.reset_retries()

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
        if self.context.spooky_subgraph.is_retries_exceeded():
            # We cannot continue if the data were not fetched.
            # It is going to make the agent fail in the next behaviour while looking for the historical data file.
            self.context.logger.error(
                "Retries were exceeded while downloading the historical data!"
            )
            # Fix: exit round via fail event and move to right round
            raise RuntimeError("Cannot continue FetchBehaviour.")

        with benchmark_tool.measure(
            self,
        ).local():
            if not self._call_failed:
                try:
                    self._current_timestamp = next(
                        cast(Iterator[int], self._timestamps_iterator)
                    )

                except StopIteration as e:

                    if len(self._pairs_hist) > 0:
                        # Store historical data to a json file.
                        try:
                            to_json_file(self._save_path, self._pairs_hist)
                        except OSError as exc:
                            self.context.logger.error(
                                f"Path '{self._save_path}' could not be found!"
                            )
                            # Fix: exit round via fail event and move to right round
                            raise exc

                        except TypeError as exc:
                            self.context.logger.error(
                                "Historical data cannot be JSON serialized!"
                            )
                            # Fix: exit round via fail event and move to right round
                            raise exc

                        # Hash the file.

                        hist_hash = self.send_file_to_ipfs_node(self._save_path)
                        self.context.logger.info(
                            f"IPFS hash for fetched data is: {hist_hash}"
                        )

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
                        return

                    self.context.logger.error("Could not download any historical data!")
                    # Fix: exit round via fail event and move to right round
                    raise RuntimeError("Cannot continue FetchBehaviour.") from e

            # Fetch block.
            fantom_api_specs = self.context.fantom_subgraph.get_spec()
            res_raw = yield from self.get_http_response(
                method=fantom_api_specs["method"],
                url=fantom_api_specs["url"],
                headers=fantom_api_specs["headers"],
                content=block_from_timestamp_q(cast(int, self._current_timestamp)),
            )
            res = self.context.fantom_subgraph.process_response(res_raw)

            try:
                self._handle_response(
                    res,
                    res_context="block",
                    keys=("blocks", 0),
                    subgraph=self.context.fantom_subgraph,
                )
            except EmptyResponseError:
                yield from self.sleep(self.params.sleep_time)
                return

            fetched_block = res["blocks"][0]

            # Fetch ETH price for block.
            res_raw = yield from self.get_http_response(
                content=eth_price_usd_q(
                    self.context.spooky_subgraph.bundle_id,
                    fetched_block["number"],
                ),
                **self._spooky_api_specs,
            )
            res = self.context.spooky_subgraph.process_response(res_raw)

            try:
                self._handle_response(
                    res,
                    res_context=f"ETH price for block {fetched_block}",
                    keys=("bundles", 0, "ethPrice"),
                    subgraph=self.context.spooky_subgraph,
                )
            except EmptyResponseError:
                yield from self.sleep(
                    self.params.sleep_time
                )  # if we end up here we unnecessarily rerun the fetch block!
                return

            eth_price = float(res["bundles"][0]["ethPrice"])

            # Fetch pool data for block.
            res_raw = yield from self.get_http_response(
                content=pairs_q(fetched_block["number"], self.params.pair_ids),
                **self._spooky_api_specs,
            )
            res = self.context.spooky_subgraph.process_response(res_raw)

            try:
                self._handle_response(
                    res,
                    res_context=f"pool data for block {fetched_block} (Showing first example)",
                    keys=("pairs", 0),
                    subgraph=self.context.spooky_subgraph,
                )
            except EmptyResponseError:
                yield from self.sleep(self.params.sleep_time)  # same as above
                return

            # Add extra fields to the pairs.
            for i in range(len(res["pairs"])):
                res["pairs"][i]["for_timestamp"] = self._current_timestamp
                res["pairs"][i]["block_number"] = fetched_block["number"]
                res["pairs"][i]["block_timestamp"] = fetched_block["timestamp"]
                res["pairs"][i]["eth_price"] = eth_price

            self._pairs_hist.extend(res["pairs"])
            self.context.logger.info(
                f"Fetched day {len(self._pairs_hist)}/{self.params.history_duration * 30}."
            )

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.spooky_subgraph.reset_retries()
        self.context.fantom_subgraph.reset_retries()


class TransformBehaviour(APYEstimationBaseState):
    """Transform historical data, i.e., convert them to a dataframe and calculate useful metrics, such as the APY."""

    state_id = "transform"
    matching_round = TransformRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._history_save_path = self._transformed_history_save_path = ""
        self._async_result: Optional[AsyncResult] = None

    def setup(self) -> None:
        """Setup behaviour."""
        pairs_hist = self.get_and_read_json(
            self.period_state.history_hash,
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            "historical_data.json",
        )

        self._transformed_history_save_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            "transformed_historical_data.csv",
        )
        create_pathdirs(self._transformed_history_save_path)

        if pairs_hist is not None:
            transform_task = TransformTask()
            task_id = self.context.task_manager.enqueue_task(
                transform_task, args=(pairs_hist,)
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

        else:
            self.context.logger.error(
                "Could not create the transform task! This will result in an error while running the round!"
            )
            # Fix: exit round via fail event and move to right round
            raise RuntimeError("Cannot continue TransformBehaviour.")

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result is None:
            self.context.logger.error(
                "Undefined behaviour encountered with `TransformTask`."
            )
            # Fix: exit round via fail event and move to right round
            raise RuntimeError("Cannot continue TransformBehaviour.")

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

        # Store the transformed data.
        transformed_history.to_csv(self._transformed_history_save_path, index=False)

        # Hash the file.
        transformed_hist_hash = self.send_file_to_ipfs_node(
            self._transformed_history_save_path
        )
        self.context.logger.info(
            f"IPFS hash for transformed data is: {transformed_hist_hash}"
        )

        # Pass the hash as a Payload.
        payload = TransformationPayload(
            self.context.agent_address,
            transformed_hist_hash,
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
        pairs_hist = self.get_and_read_hist(
            self.period_state.transformed_history_hash,
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            "transformed_historical_data.csv",
        )

        (y_train, y_test), pair_name = prepare_pair_data(
            pairs_hist, self.params.pair_ids[0]
        )
        self.context.logger.info("Data have been preprocessed.")
        self.context.logger.info(f"y_train: {y_train.to_string()}")
        self.context.logger.info(f"y_test: {y_test.to_string()}")

        # Store and hash the preprocessed data.
        hashes = []
        for filename, split in {"train": y_train, "test": y_test}.items():
            save_path = os.path.join(
                self.context._get_agent_context().data_dir,  # pylint: disable=W0212
                self.params.pair_ids[0],
                f"y_{filename}.csv",
            )
            create_pathdirs(save_path)
            split.to_csv(save_path, index=False)
            split_hash = self.send_file_to_ipfs_node(save_path)
            self.context.logger.info(f"IPFS hash for {filename} data is: {split_hash}")
            hashes.append(split_hash)

        # Pass the hash as a Payload.
        payload = PreprocessPayload(
            self.context.agent_address, pair_name, hashes[0], hashes[1]
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

    def setup(self) -> None:
        """Setup behaviour."""
        # Load training data.
        training_data_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
        )
        y = self.get_and_read_csv(
            self.period_state.train_hash, training_data_path, "y_train.csv"
        )

        optimize_task = OptimizeTask()
        task_id = self.context.task_manager.enqueue_task(
            optimize_task,
            args=(
                y.values.ravel(),
                self.period_state.most_voted_randomness,
            ),
            kwargs=self.params.optimizer_params,
        )
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result is None:
            self.context.logger.error(
                "Undefined behaviour encountered with `OptimizationTask`."
            )
            # Fix: exit round via fail event and move to right round
            raise RuntimeError("Cannot continue OptimizationTask.")

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
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
            "best_params.json",
        )
        create_pathdirs(best_params_save_path)

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

        try:
            to_json_file(best_params_save_path, best_params)

        except OSError as e:  # pragma: nocover
            self.context.logger.error(
                f"Path '{best_params_save_path}' could not be found!"
            )
            # Fix: exit round via fail event and move to right round
            raise e

        except TypeError as e:  # pragma: nocover
            self.context.logger.error("Params cannot be JSON serialized!")
            # Fix: exit round via fail event and move to right round
            raise e

        # Hash the file.
        best_params_hash = self.send_file_to_ipfs_node(best_params_save_path)
        self.context.logger.info(f"IPFS hash for best params is: {best_params_hash}")

        # Pass the best params hash as a Payload.
        payload = OptimizationPayload(self.context.agent_address, best_params_hash)

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

    def setup(self) -> None:
        """Setup behaviour."""
        y: Union[np.ndarray, List[np.ndarray]] = []

        # Load the best params from the optimization results.
        best_params_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
        )
        best_params = cast(
            Dict[str, Any],
            self.get_and_read_json(
                self.period_state.params_hash, best_params_path, "best_params.json"
            ),
        )

        # Load training data.
        if self.period_state.full_training:
            for split in ("train", "test"):
                path = os.path.join(
                    self.context._get_agent_context().data_dir,  # pylint: disable=W0212
                    self.params.pair_ids[0],
                )
                df = self.get_and_read_csv(
                    getattr(self.period_state, f"{split}_hash"), path, f"y_{split}.csv"
                )
                cast(List[np.ndarray], y).append(df.values.ravel())

            y = np.concatenate(y)

        else:
            path = os.path.join(
                self.context._get_agent_context().data_dir,  # pylint: disable=W0212
                self.params.pair_ids[0],
            )
            y = self.get_and_read_csv(
                self.period_state.train_hash, path, "y_train.csv"
            ).values.ravel()

        train_task = TrainTask()
        task_id = self.context.task_manager.enqueue_task(
            train_task, args=(y,), kwargs=best_params
        )
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result is None:
            self.context.logger.error(
                "Undefined behaviour encountered with `TrainTask`."
            )
            # Fix: exit round via fail event and move to right round
            raise RuntimeError("Cannot continue TrainTask.")

        if not self._async_result.ready():
            self.context.logger.debug("The training task is not finished yet.")
            yield from self.sleep(self.params.sleep_time)
            return

        # Get the trained estimator.
        completed_task = self._async_result.get()
        forecaster = cast(Pipeline, completed_task)
        self.context.logger.info("Training has finished.")

        # Store the results.
        prefix = "fully_trained_" if self.period_state.full_training else ""
        forecaster_save_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
            f"{prefix}forecaster.joblib",
        )
        create_pathdirs(forecaster_save_path)
        save_forecaster(forecaster_save_path, forecaster)

        # Hash the file.
        model_hash = self.send_file_to_ipfs_node(forecaster_save_path)
        self.context.logger.info(
            f"IPFS hash for {prefix}forecasting model is: {model_hash}"
        )

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

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load test data.
        y: Dict[str, Optional[np.ndarray]] = {"y_train": None, "y_test": None}

        for split in ("train", "test"):
            path = os.path.join(
                self.context._get_agent_context().data_dir,  # pylint: disable=W0212
                self.params.pair_ids[0],
            )
            df = self.get_and_read_csv(
                getattr(self.period_state, f"{split}_hash"), path, f"y_{split}.csv"
            )
            y[f"y_{split}"] = df.values.ravel()

        model_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
        )
        forecaster = self.get_and_read_forecaster(
            self.period_state.model_hash, model_path, "forecaster.joblib"
        )

        test_task = TestTask()
        task_args = (
            forecaster,
            y["y_train"],
            y["y_test"],
            self.period_state.pair_name,
            self.params.testing["steps_forward"],
        )
        task_id = self.context.task_manager.enqueue_task(test_task, task_args)
        self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._async_result is None:
            self.context.logger.error(
                "Undefined behaviour encountered with `TestTask`."
            )
            # Fix: exit round via fail event and move to right round
            raise RuntimeError("Cannot continue TestTask.")

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
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
            "test_report.json",
        )
        create_pathdirs(report_save_path)

        try:
            to_json_file(report_save_path, report)

        except OSError as e:  # pragma: nocover
            self.context.logger.error(f"Path '{report_save_path}' could not be found!")
            # Fix: exit round via fail event and move to right round
            raise e

        except TypeError as e:  # pragma: nocover
            self.context.logger.error("Report cannot be JSON serialized!")
            # Fix: exit round via fail event and move to right round
            raise e

        # Hash the file.
        report_hash = self.send_file_to_ipfs_node(report_save_path)
        self.context.logger.info(f"IPFS hash for test report is: {report_hash}")

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
        model_path = os.path.join(
            self.context._get_agent_context().data_dir,  # pylint: disable=W0212
            self.params.pair_ids[0],
        )
        forecaster = self.get_and_read_forecaster(
            self.period_state.model_hash,
            model_path,
            "fully_trained_forecaster.joblib",
        )

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

    cycle = False

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
        if self.cycle and self.period_state.is_most_voted_estimate_set:
            self.context.logger.info(
                f"Finalized estimate: {self.period_state.most_voted_estimate}. Resetting and pausing!"
            )
            # Fix: add pausing
            benchmark_tool.save()
        elif self.cycle and not self.period_state.is_most_voted_estimate_set:
            self.context.logger.info("Finalized estimate not available. Resetting!")
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


class CycleResetBehaviour(BaseResetBehaviour):
    """Cycle reset state."""

    matching_round = CycleResetRound
    state_id = "cycle_reset"
    cycle = True


class APYEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the APY estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = APYEstimationAbciApp
    behaviour_states: Set[Type[APYEstimationBaseState]] = {
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        FetchBehaviour,
        TransformBehaviour,
        PreprocessBehaviour,  # type: ignore
        RandomnessBehaviour,  # type: ignore
        OptimizeBehaviour,
        TrainBehaviour,
        TestBehaviour,
        EstimateBehaviour,  # type: ignore
        ResetBehaviour,  # type: ignore
        CycleResetBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
