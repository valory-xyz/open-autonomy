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
import json
import os
import re
from abc import ABC
from multiprocessing.pool import AsyncResult
from typing import (
    Any,
    Dict,
    Generator,
    Iterator,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import numpy as np
import pandas as pd

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.io.load import SupportedFiletype
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.utils import VerifyDrand
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    PoolIdToForecasterType,
    PoolIdToTestReportType,
    PoolIdToTrainDataType,
    PoolToHyperParamsType,
)
from packages.valory.skills.apy_estimation_abci.ml.optimization import (
    PoolToHyperParamsWithStatusType,
)
from packages.valory.skills.apy_estimation_abci.ml.preprocessing import (
    TrainTestSplitType,
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
    PrepareBatchRound,
    PreprocessRound,
    RandomnessRound,
    SynchronizedData,
    TestRound,
    TrainRound,
    TransformRound,
    UpdateForecasterRound,
)
from packages.valory.skills.apy_estimation_abci.tasks import (
    EstimateTask,
    OptimizeTask,
    PrepareBatchTask,
    PreprocessTask,
    TestTask,
    TrainTask,
    TransformTask,
    UpdateTask,
)
from packages.valory.skills.apy_estimation_abci.tools.etl import ResponseItemType
from packages.valory.skills.apy_estimation_abci.tools.general import (
    gen_unix_timestamps,
    sec_to_unit,
    unit_amount_from_sec,
)
from packages.valory.skills.apy_estimation_abci.tools.io import load_hist
from packages.valory.skills.apy_estimation_abci.tools.queries import (
    block_from_number_q,
    block_from_timestamp_q,
    eth_price_usd_q,
    latest_block_q,
    pairs_q,
)


NON_INDEXED_BLOCK_RE = (
    r"Failed to decode `block.number` value: `subgraph QmPJbGjktGa7c4UYWXvDRajPxpuJBSZxeQK5siNT3VpthP has only "
    r"indexed up to block number (\d+) and data for block number \d+ is therefore not yet available`"
)


class APYEstimationBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the APY estimation skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> APYParams:
        """Return the params."""
        return cast(APYParams, self.context.params)

    def load_split(self, split: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Load a split of the data."""
        split_path = os.path.join(
            self.context.data_dir,
            f"y_{split}",
            f"period_{self.synchronized_data.period_count}",
        )
        return self.get_from_ipfs(
            getattr(self.synchronized_data, f"{split}_hash"),
            split_path,
            multiple=True,
            filetype=SupportedFiletype.CSV,
        )


class FetchBehaviour(
    APYEstimationBaseBehaviour
):  # pylint: disable=too-many-instance-attributes
    """Observe historical data."""

    behaviour_id = "fetch"
    matching_round = CollectHistoryRound
    batch = False

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._save_path = ""
        self._spooky_api_specs: Dict[str, Any] = dict()
        self._timestamps_iterator: Optional[Iterator[int]] = None
        self._current_timestamp: Optional[int] = None
        self._call_failed = False
        self._pairs_hist: ResponseItemType = []
        self._hist_hash: Optional[str] = None
        self._unit = ""
        self._total_unit_amount = 0

    @property
    def current_unit(self) -> int:
        """Get the number of the currently downloaded unit."""
        return int(len(self._pairs_hist) / len(self.params.pair_ids))

    def setup(self) -> None:
        """Set the behaviour up."""
        if self.params.end is None or self.batch:
            last_timestamp = cast(
                SharedState, self.context.state
            ).round_sequence.abci_app.last_timestamp
            self.params.end = int(calendar.timegm(last_timestamp.timetuple()))

        self._unit = sec_to_unit(self.params.interval)
        self._total_unit_amount = int(
            unit_amount_from_sec(self.params.end - self.params.start, self._unit)
        )

        filename = "historical_data"

        if self.batch:
            filename += f"_batch_{self.params.end}"
            self._timestamps_iterator = iter((self.params.end,))
        else:
            self._timestamps_iterator = gen_unix_timestamps(
                self.params.start, self.params.interval, self.params.end
            )

        self._save_path = os.path.join(
            self.context.data_dir,
            f"{filename}_period_{self.synchronized_data.period_count}.json",
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
            # manually call clean-up, as it is not called by the framework if a `StopIteration` is not raised
            self.clean_up()

        # if none of the above (call failed and we can retry), the current timestamp will remain the same.

    def _handle_response(
        self,
        res: Optional[Dict],
        res_context: str,
        keys: Tuple[Union[str, int], ...],
        subgraph: ApiSpecs,
        sleep_on_fail: bool = True,
    ) -> Generator[None, None, Optional[Any]]:
        """Handle a response from a subgraph.

        :param res: the response to handle.
        :param res_context: the context of the current response.
        :param keys: keys to get the information from the response.
        :param subgraph: api specs.
        :param sleep_on_fail: whether we want to sleep if we fail to get the response's result.
        :return: the response's result, using the given keys. `None` if response is `None` (has failed).
        :yield: None
        """
        if res is None:
            self.context.logger.error(
                f"Could not get {res_context} from {subgraph.api_id}"
            )

            self._call_failed = True
            subgraph.increment_retries()
            if sleep_on_fail:
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

    def _fetch_block(
        self, number: Optional[int] = None
    ) -> Generator[None, None, Optional[Dict[str, int]]]:
        """Fetch block."""
        fantom_api_specs = self.context.fantom_subgraph.get_spec()
        if number is not None:
            query = block_from_number_q(number)
        else:
            query = (
                latest_block_q()
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

        return fetched_block

    def _fetch_eth_price(
        self, block: Dict[str, int]
    ) -> Generator[None, None, Tuple[HttpMessage, Optional[float]]]:
        """Fetch ETH price for block."""
        res_raw = yield from self.get_http_response(
            content=eth_price_usd_q(
                self.context.spooky_subgraph.bundle_id,
                block["number"],
            ),
            **self._spooky_api_specs,
        )
        res = self.context.spooky_subgraph.process_response(res_raw)

        eth_price = yield from self._handle_response(
            res,
            res_context=f"ETH price for block {block}",
            keys=("bundles", 0, "ethPrice"),
            subgraph=self.context.spooky_subgraph,
            sleep_on_fail=False,
        )

        return res_raw, eth_price

    def _check_non_indexed_block(
        self, res_raw: HttpMessage
    ) -> Generator[None, None, Optional[Tuple[Dict[str, int], float]]]:
        """Check if we received a non-indexed block error and try to get the ETH price for the latest indexed block."""
        res = self.context.spooky_subgraph.process_non_indexed_error(res_raw)
        latest_indexed_block_error = yield from self._handle_response(
            res,
            res_context="indexing error that will be attempted to be handled",
            keys=(0, "message"),
            subgraph=self.context.spooky_subgraph,
        )
        if latest_indexed_block_error is None:
            return None

        match = re.match(NON_INDEXED_BLOCK_RE, latest_indexed_block_error)
        if match is None:
            self.context.logger.warning(
                "Attempted to handle an indexing error, but could not extract the latest indexed block!"
            )
            return None

        latest_indexed_block_number = int(match.group(1))
        # we set the last digit to 0, so that it is more possible for the agents to reach to a consensus
        # without requiring an extra round.
        latest_indexed_block_number -= latest_indexed_block_number % 10

        # Fetch latest indexed block.
        latest_indexed_block = yield from self._fetch_block(latest_indexed_block_number)
        if latest_indexed_block is None:
            return None

        # Fetch ETH price for latest indexed block.
        _, eth_price = yield from self._fetch_eth_price(latest_indexed_block)
        if eth_price is None:
            return None

        return latest_indexed_block, eth_price

    def _fetch_eth_price_safely(
        self, block: Dict[str, int]
    ) -> Generator[None, None, Optional[Tuple[Dict[str, int], float]]]:
        """
        Fetch ETH price for a block.

        If the block is not indexed yet, fetch the latest indexed block and the ETH price for that block.

        :param block: the block for which we will try to fetch the ETH price.
        :return: the same block or the latest indexed and the corresponding ETH price.
        :yield: None
        """
        res_raw, eth_price = yield from self._fetch_eth_price(block)

        if eth_price is None:
            check_result = yield from self._check_non_indexed_block(res_raw)
            if check_result is None:
                return None
            block, eth_price = check_result

        return block, eth_price

    def _fetch_pairs(
        self, block: Dict[str, int]
    ) -> Generator[None, None, Optional[ResponseItemType]]:
        """Fetch pool data for block."""
        res_raw = yield from self.get_http_response(
            content=pairs_q(block["number"], self.params.pair_ids),
            **self._spooky_api_specs,
        )
        res = self.context.spooky_subgraph.process_response(res_raw)

        pairs = yield from self._handle_response(
            res,
            res_context=f"pool data for block {block}",
            keys=("pairs",),
            subgraph=self.context.spooky_subgraph,
        )

        return pairs

    def _fetch_batch(self) -> Generator[None, None, None]:
        """Fetch a single batch of the historical data."""
        block = yield from self._fetch_block()
        if block is None:
            return

        check_result = yield from self._fetch_eth_price_safely(block)
        if check_result is None:
            return
        block, eth_price = check_result

        pairs = yield from self._fetch_pairs(block)
        if pairs is None:
            return

        # Add extra fields to the pairs.
        for i in range(len(pairs)):  # pylint: disable=C0200
            pairs[i]["forTimestamp"] = str(self._current_timestamp)
            pairs[i]["blockNumber"] = str(block["number"])
            pairs[i]["blockTimestamp"] = str(block["timestamp"])
            pairs[i]["ethPrice"] = str(eth_price)

        self._pairs_hist.extend(pairs)

        if not self.batch:
            self.context.logger.info(
                f"Fetched {self._unit} {self.current_unit}/{self._total_unit_amount}."
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
        - Go to the next behaviour (set done event).
        """
        self._set_current_timestamp()

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            if self._current_timestamp is not None:
                yield from self._fetch_batch()
                return

            if self.current_unit == 0:
                self.context.logger.error("Could not download any historical data!")
                self._hist_hash = ""

            if (
                self.current_unit > 0
                and self.current_unit != self._total_unit_amount
                and not self.batch
            ):
                # Here, we continue without having all the pairs downloaded, because of a network issue.
                self.context.logger.warning(
                    "Will continue with partially downloaded historical data!"
                )

            if self.current_unit > 0:
                # Send the file to IPFS and get its hash.
                self._hist_hash = self.send_to_ipfs(
                    self._save_path, self._pairs_hist, filetype=SupportedFiletype.JSON
                )

            # Pass the hash as a Payload.
            payload = FetchingPayload(
                self.context.agent_address,
                self._hist_hash,
            )

            # Finish behaviour.
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
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


class FetchBatchBehaviour(FetchBehaviour):  # pylint: disable=too-many-ancestors
    """Observe the latest batch of historical data."""

    behaviour_id = "fetch_batch"
    matching_round = CollectLatestHistoryBatchRound
    batch = True


class TransformBehaviour(APYEstimationBaseBehaviour):
    """Transform historical data, i.e., convert them to a dataframe and calculate useful metrics, such as the APY."""

    behaviour_id = "transform"
    matching_round = TransformRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._transformed_history_save_path = ""
        self._async_result: Optional[AsyncResult] = None
        self._pairs_hist: Optional[ResponseItemType] = None
        self._transformed_hist_hash: Optional[str] = None
        self._latest_observations_hist_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        self._pairs_hist = self.get_from_ipfs(
            self.synchronized_data.history_hash,
            self.context.data_dir,
            filename=f"historical_data_period_{self.synchronized_data.period_count}.json",
            filetype=SupportedFiletype.JSON,
        )

        self._transformed_history_save_path = os.path.join(
            self.context.data_dir,
            f"transformed_historical_data_period_{self.synchronized_data.period_count}.csv",
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
                filetype=SupportedFiletype.CSV,
            )

            # Get the latest observation for each pool id.
            latest_observations = transformed_history.groupby("id").last().reset_index()
            # Send the latest observations to IPFS and get the hash.
            latest_observations_save_path = os.path.join(
                self.context.data_dir,
                f"latest_observations_period_{self.synchronized_data.period_count}.csv",
            )
            self._latest_observations_hist_hash = self.send_to_ipfs(
                latest_observations_save_path,
                latest_observations,
                filetype=SupportedFiletype.CSV,
            )

        # Pass the hashes as a Payload.
        payload = TransformationPayload(
            self.context.agent_address,
            self._transformed_hist_hash,
            self._latest_observations_hist_hash,
        )

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PreprocessBehaviour(APYEstimationBaseBehaviour):
    """Preprocess historical data (train-test split)."""

    behaviour_id = "preprocess"
    matching_round = PreprocessRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._preprocessed_pairs_save_path = ""
        self._async_result: Optional[AsyncResult] = None
        self._pairs_hist: Optional[ResponseItemType] = None
        self._preprocessed_pairs_hashes: Dict[str, Optional[str]] = {
            "train_hash": None,
            "test_hash": None,
        }

    def setup(self) -> None:
        """Setup behaviour."""
        # get the transformed historical data.
        self._pairs_hist = self.get_from_ipfs(
            self.synchronized_data.transformed_history_hash,
            self.context.data_dir,
            filename=f"transformed_historical_data_period_{self.synchronized_data.period_count}.csv",
            custom_loader=load_hist,
        )

        if self._pairs_hist is not None:
            preprocess_task = PreprocessTask()
            task_id = self.context.task_manager.enqueue_task(
                preprocess_task, args=(self._pairs_hist,)
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

            # Get the preprocessed data from the task.
            completed_task = self._async_result.get()
            train_splits, test_splits = cast(TrainTestSplitType, completed_task)
            self.context.logger.info(
                f"Data have been preprocessed:\nTrain splits {train_splits}\nTest splits{test_splits}"
            )

            # Store and hash the preprocessed data.
            for split_name, split in {
                "train": train_splits,
                "test": test_splits,
            }.items():
                save_path = os.path.join(
                    self.context.data_dir,
                    f"y_{split_name}",
                    f"period_{self.synchronized_data.period_count}",
                )

                split_hash = self.send_to_ipfs(
                    save_path, split, multiple=True, filetype=SupportedFiletype.CSV
                )
                self._preprocessed_pairs_hashes[f"{split_name}_hash"] = split_hash

        # Pass the hashes as a Payload.
        payload = PreprocessPayload(
            self.context.agent_address, **self._preprocessed_pairs_hashes
        )

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PrepareBatchBehaviour(APYEstimationBaseBehaviour):
    """Transform and preprocess batch data."""

    behaviour_id = "prepare_batch"
    matching_round = PrepareBatchRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._batches: Tuple[Optional[pd.DataFrame], Optional[ResponseItemType]] = (
            None,
            None,
        )
        self._async_result: Optional[AsyncResult] = None
        self._prepared_batches_save_path = ""
        self._prepared_batches_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # These are the previous and the currently fetched batches. They are required for the task.
        self._batches = (
            self.get_from_ipfs(
                self.synchronized_data.latest_observation_hist_hash,
                self.context.data_dir,
                filename=f"latest_observations_period_{self.synchronized_data.period_count - 1}.csv",
                custom_loader=load_hist,
            ),
            self.get_from_ipfs(
                self.synchronized_data.batch_hash,
                self.context.data_dir,
                filename=f"historical_data_batch_{self.params.end}"
                f"_period_{self.synchronized_data.period_count}.json",
                filetype=SupportedFiletype.JSON,
            ),
        )

        if not any(batch is None for batch in self._batches):
            prepare_batch_task = PrepareBatchTask()
            task_id = self.context.task_manager.enqueue_task(
                prepare_batch_task, self._batches
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

        self._prepared_batches_save_path = os.path.join(
            self.context.data_dir,
            f"latest_observations_period_{self.synchronized_data.period_count}.csv",
        )

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(batch is None for batch in self._batches):
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The prepare batch task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the prepared batches from the task.
            prepared_batches = self._async_result.get()
            self.context.logger.info(
                f"Batches have been prepared:\n{prepared_batches.to_string()}"
            )

            # Send the file to IPFS and get its hash.
            self._prepared_batches_hash = self.send_to_ipfs(
                self._prepared_batches_save_path,
                prepared_batches,
                filetype=SupportedFiletype.CSV,
            )

        # Pass the hash as a Payload.
        payload = BatchPreparationPayload(
            self.context.agent_address,
            self._prepared_batches_hash,
        )

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RandomnessBehaviour(APYEstimationBaseBehaviour):
    """Get randomness value from `drnand`."""

    behaviour_id = "randomness"
    matching_round = RandomnessRound

    def async_act(self) -> Generator:
        """Get randomness value from `drnand`."""
        if self.context.randomness_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
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
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.randomness_api.reset_retries()


class OptimizeBehaviour(APYEstimationBaseBehaviour):
    """Run an optimization study based on the training data."""

    behaviour_id = "optimize"
    matching_round = OptimizeRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._y: Optional[Dict[str, pd.DataFrame]] = None
        self._current_id: Optional[str] = None
        self._best_params_with_status_iterator: Iterator[str] = iter("")
        self._best_params_with_status: PoolToHyperParamsWithStatusType = {}
        self._best_params_per_pool: PoolToHyperParamsType = {}
        self._best_params_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load training data.
        self._y = self.load_split("train")

        if self._y is not None:
            optimize_task = OptimizeTask()
            task_id = self.context.task_manager.enqueue_task(
                optimize_task,
                args=(
                    self._y,
                    self.synchronized_data.most_voted_randomness,
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

            if self._current_id is None:
                # Get the best parameters result.
                self._best_params_with_status = self._async_result.get()
                self._best_params_with_status_iterator = iter(
                    self._best_params_with_status.keys()
                )

            self._current_id = cast(
                str, next(self._best_params_with_status_iterator, "")
            )
            if self._current_id != "":
                best_params, study_succeeded = self._best_params_with_status[
                    self._current_id
                ]
                self._best_params_per_pool[self._current_id] = best_params
                if not study_succeeded:
                    self.context.logger.warning(
                        f"The optimization could not be done for pool `{self._current_id}`! "
                        "Please make sure that there is a sufficient number of data "
                        "for the optimization procedure. Parameters have been set randomly!"
                    )
                return

            self.context.logger.info(
                "Optimization has finished. Showing the results:\n"
                f"{self._best_params_per_pool}"
            )

            # Store the best params from the results.
            best_params_save_path = os.path.join(
                self.context.data_dir,
                "best_params",
                f"period_{self.synchronized_data.period_count}",
            )
            self._best_params_hash = self.send_to_ipfs(
                best_params_save_path,
                self._best_params_per_pool,
                multiple=True,
                filetype=SupportedFiletype.JSON,
            )

        # Pass the best params hash as a Payload.
        payload = OptimizationPayload(
            self.context.agent_address, self._best_params_hash
        )

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class TrainBehaviour(APYEstimationBaseBehaviour):
    """Train an estimator."""

    behaviour_id = "train"
    matching_round = TrainRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._best_params: Optional[PoolToHyperParamsType] = None
        self._y: Optional[PoolIdToTrainDataType] = None
        self._models_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load the best params from the optimization results.
        best_params_path = os.path.join(
            self.context.data_dir,
            "best_params",
            f"period_{self.synchronized_data.period_count}",
        )
        self._best_params = self.get_from_ipfs(
            self.synchronized_data.params_hash,
            best_params_path,
            multiple=True,
            filetype=SupportedFiletype.JSON,
        )

        pool_to_train_data = self.load_split("train")
        if pool_to_train_data is not None:
            self._y = {
                pool_id: pool_splits.values.ravel()
                for pool_id, pool_splits in pool_to_train_data.items()
            }

        if self.synchronized_data.full_training and self._y is not None:
            pool_to_test_data = self.load_split("test")
            if pool_to_test_data is None:  # pragma: nocover
                self._y = None
            else:
                self._y.update(
                    (
                        pool_id,
                        np.concatenate(
                            (self._y[pool_id], pool_split_data.values.ravel())
                        ),
                    )
                    for pool_id, pool_split_data in pool_to_test_data.items()
                )

        if not any(arg is None for arg in (self._y, self._best_params)):
            train_task = TrainTask()
            task_id = self.context.task_manager.enqueue_task(
                train_task, args=(self._y, self._best_params)
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
            forecasters = self._async_result.get()
            self.context.logger.info("Training has finished.")

            prefix = "fully_trained_" if self.synchronized_data.full_training else ""
            forecaster_save_path = os.path.join(
                self.context.data_dir,
                f"{prefix}forecasters",
                f"period_{self.synchronized_data.period_count}",
            )

            # Send the file to IPFS and get its hash.
            self._models_hash = self.send_to_ipfs(
                forecaster_save_path,
                forecasters,
                multiple=True,
                filetype=SupportedFiletype.PM_PIPELINE,
            )

        payload = TrainingPayload(self.context.agent_address, self._models_hash)

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class TestBehaviour(APYEstimationBaseBehaviour):
    """Test an estimator."""

    behaviour_id = "test"
    matching_round = TestRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._y_train: Optional[PoolIdToTrainDataType] = None
        self._y_test: Optional[PoolIdToTrainDataType] = None
        self._forecasters: Optional[PoolIdToForecasterType] = None
        self._report_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load data.
        for split in ("train", "test"):
            y = self.load_split(split)
            if y is not None:
                setattr(
                    self,
                    f"_y_{split}",
                    {
                        pool_id: pool_splits.values.ravel()
                        for pool_id, pool_splits in y.items()
                    },
                )

        models_path = os.path.join(
            self.context.data_dir,
            "forecasters",
            f"period_{self.synchronized_data.period_count}",
        )

        self._forecasters = self.get_from_ipfs(
            self.synchronized_data.models_hash,
            models_path,
            multiple=True,
            filetype=SupportedFiletype.PM_PIPELINE,
        )

        if not any(
            arg is None for arg in (self._y_train, self._y_test, self._forecasters)
        ):
            test_task = TestTask()
            task_args = (
                self._forecasters,
                self._y_train,
                self._y_test,
            )
            task_id = self.context.task_manager.enqueue_task(
                test_task, task_args, self.params.testing
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(
            arg is None for arg in (self._y_train, self._y_test, self._forecasters)
        ):
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The testing task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the test report.
            completed_task = self._async_result.get()
            report = cast(PoolIdToTestReportType, completed_task)
            self.context.logger.info(
                "Testing has finished. Report follows:\n"
                f"{json.dumps(report, sort_keys=False, indent=4)}"
            )

            # Store the results.
            report_save_path = os.path.join(
                self.context.data_dir,
                "reports",
                f"period_{self.synchronized_data.period_count}",
            )
            # Send the file to IPFS and get its hash.
            self._report_hash = self.send_to_ipfs(
                report_save_path, report, multiple=True, filetype=SupportedFiletype.JSON
            )

        # Pass the hash and the best trial as a Payload.
        payload = TestingPayload(self.context.agent_address, self._report_hash)

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class UpdateForecasterBehaviour(APYEstimationBaseBehaviour):
    """Update an estimator."""

    behaviour_id = "update"
    matching_round = UpdateForecasterRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._y: Optional[PoolIdToTrainDataType] = None
        self._forecasters_folder: str = os.path.join(
            self.context.data_dir,
            "fully_trained_forecasters",
            "period_",
        )
        self._forecasters: Optional[PoolIdToForecasterType] = None
        self._models_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load data batch.
        self._y = self.get_from_ipfs(
            self.synchronized_data.latest_observation_hist_hash,
            self.context.data_dir,
            filename=f"latest_observations_period_{self.synchronized_data.period_count}.csv",
            filetype=SupportedFiletype.CSV,
        )

        # Load forecasters.
        self._forecasters = self.get_from_ipfs(
            self.synchronized_data.models_hash,
            self._forecasters_folder + str(self.synchronized_data.period_count - 1),
            multiple=True,
            filetype=SupportedFiletype.PM_PIPELINE,
        )

        if not any(arg is None for arg in (self._y, self._forecasters)):
            update_task = UpdateTask()
            task_id = self.context.task_manager.enqueue_task(
                update_task, args=(self._y, self._forecasters)
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if not any(arg is None for arg in (self._y, self._forecasters)):
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The updating task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            self.context.logger.info("Forecasters have been updated.")

            # Send the file to IPFS and get its hash.
            self._models_hash = self.send_to_ipfs(
                self._forecasters_folder + str(self.synchronized_data.period_count),
                self._forecasters,
                multiple=True,
                filetype=SupportedFiletype.PM_PIPELINE,
            )

        payload = UpdatePayload(self.context.agent_address, self._models_hash)

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class EstimateBehaviour(APYEstimationBaseBehaviour):
    """Estimate APY."""

    behaviour_id = "estimate"
    matching_round = EstimateRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        self._async_result: Optional[AsyncResult] = None
        self._forecasters: Optional[PoolIdToForecasterType] = None
        self._estimations_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load forecasters.
        forecasters_folder: str = os.path.join(
            self.context.data_dir,
            "fully_trained_forecasters",
            f"period_{self.synchronized_data.period_count}",
        )
        self._forecasters = self.get_from_ipfs(
            self.synchronized_data.models_hash,
            forecasters_folder,
            multiple=True,
            filetype=SupportedFiletype.PM_PIPELINE,
        )

        if self._forecasters is not None:
            estimate_task = EstimateTask()
            task_id = self.context.task_manager.enqueue_task(
                estimate_task, args=(self._forecasters,), kwargs=self.params.estimation
            )
            self._async_result = self.context.task_manager.get_task_result(task_id)

    def async_act(self) -> Generator:
        """Do the action."""
        if self._forecasters is not None:
            self._async_result = cast(AsyncResult, self._async_result)
            if not self._async_result.ready():
                self.context.logger.debug("The estimating task is not finished yet.")
                yield from self.sleep(self.params.sleep_time)
                return

            # Get the estimates.
            estimates = self._async_result.get()
            self.context.logger.info(
                "Estimates have been received:\n" f"{estimates.to_string()}"
            )
            self.context.logger.info("Estimates have been received.")

            # Send the file to IPFS and get its hash.
            estimations_path = os.path.join(
                self.context.data_dir,
                f"estimations_period_{self.synchronized_data.period_count}.csv",
            )
            self._estimations_hash = self.send_to_ipfs(
                estimations_path,
                estimates,
                filetype=SupportedFiletype.CSV,
            )

        payload = EstimatePayload(self.context.agent_address, self._estimations_hash)

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class BaseResetBehaviour(APYEstimationBaseBehaviour):
    """Reset behaviour."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Trivially log the behaviour.
        - Sleep for configured interval.
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """
        if (
            self.behaviour_id == "cycle_reset"
            and self.synchronized_data.is_most_voted_estimate_set
        ):
            # Load estimations.
            estimations = self.get_from_ipfs(
                self.synchronized_data.estimates_hash,
                self.context.data_dir,
                filename=f"estimations_period_{self.synchronized_data.period_count}.csv",
                filetype=SupportedFiletype.CSV,
            )
            if estimations is not None:
                self.context.logger.info(
                    f"Finalized estimates: {estimations.to_string()}. Resetting and pausing!"
                )
            else:
                self.context.logger.error(
                    "There was an error while trying to fetch and load the estimations from IPFS!"
                )
            self.context.logger.info(
                f"Estimation will happen again in {self.params.observation_interval} seconds."
            )
            yield from self.sleep(self.params.observation_interval)
            self.context.benchmark_tool.save()
        elif (
            self.behaviour_id == "cycle_reset"
            and not self.synchronized_data.is_most_voted_estimate_set
        ):
            self.context.logger.info("Finalized estimate not available. Resetting!")
        elif self.behaviour_id == "fresh_model_reset":
            self.context.logger.info("Resetting to create a fresh forecasting model!")
        else:  # pragma: nocover
            raise RuntimeError(
                f"BaseResetBehaviour not used correctly. Got {self.behaviour_id}. "
                f"Allowed behaviour ids are `cycle_reset` and `fresh_model_reset`."
            )

        payload = ResetPayload(
            self.context.agent_address, self.synchronized_data.period_count
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class FreshModelResetBehaviour(  # pylint: disable=too-many-ancestors
    BaseResetBehaviour
):
    """Reset behaviour to start with a fresh model."""

    matching_round = FreshModelResetRound
    behaviour_id = "fresh_model_reset"


class CycleResetBehaviour(BaseResetBehaviour):  # pylint: disable=too-many-ancestors
    """Cycle reset behaviour."""

    matching_round = CycleResetRound
    behaviour_id = "cycle_reset"


class EstimatorRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the APY estimation behaviour."""

    initial_behaviour_cls = FetchBehaviour
    abci_app_cls = APYEstimationAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        FetchBehaviour,
        FetchBatchBehaviour,
        TransformBehaviour,
        PreprocessBehaviour,
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
