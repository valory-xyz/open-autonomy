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
from dataclasses import dataclass
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

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.utils import VerifyDrand
from packages.valory.skills.apy_estimation_abci.constants import (
    BEST_PARAMS_PATH,
    ESTIMATIONS_PATH_TEMPLATE,
    FORECASTERS_PATH,
    FULLY_TRAINED_FORECASTERS_PATH,
    HISTORICAL_DATA_BATCH_PATH_TEMPLATE,
    HISTORICAL_DATA_PATH_TEMPLATE,
    LATEST_OBSERVATIONS_PATH_TEMPLATE,
    PERIOD_SPECIFIER_TEMPLATE,
    REPORTS_PATH,
    TRANSFORMED_HISTORICAL_DATA_PATH_TEMPLATE,
    Y_SPLIT_TEMPLATE,
)
from packages.valory.skills.apy_estimation_abci.io_.load import Loader
from packages.valory.skills.apy_estimation_abci.io_.store import (
    ExtendedSupportedFiletype,
    Storer,
)
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
from packages.valory.skills.apy_estimation_abci.models import (
    APYParams,
    DEXSubgraph,
    SharedState,
    SubgraphsMixin,
)
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
from packages.valory.skills.apy_estimation_abci.tools.io_ import load_hist
from packages.valory.skills.apy_estimation_abci.tools.queries import (
    block_from_number_q,
    block_from_timestamp_q,
    eth_price_usd_q,
    existing_pairs_q,
    latest_block_q,
    pairs_q,
)


NON_INDEXED_BLOCK_RE = (
    r"Failed to decode `block.number` value: `subgraph \w{46} has only "
    r"indexed up to block number (\d+) and data for block number \d+ is therefore not yet available`"
)


class APYEstimationBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the APY estimation skill."""

    def __init__(self, **kwargs: Any):
        """Initialize an APY base behaviour."""
        super().__init__(**kwargs, loader_cls=Loader, storer_cls=Storer)

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> APYParams:
        """Return the params."""
        return cast(APYParams, self.context.params)

    def period_specifier(self, previous_period: bool = False) -> str:
        """Return the period specifier for the filenames."""
        period_count = self.synchronized_data.period_count
        if previous_period:
            period_count -= 1

        period_specifier = PERIOD_SPECIFIER_TEMPLATE.substitute(
            period_count=period_count
        )

        return period_specifier

    def with_period_specifier(self, path: str, previous_period: bool = False) -> str:
        """Return the given path with the period specifier appended."""
        return os.path.join(path, self.period_specifier(previous_period))

    def from_data_dir(self, path: str) -> str:
        """Return the given path appended to the data dir."""
        return os.path.join(self.context.data_dir, path)

    def from_data_dir_with_period_specifier(
        self, path: str, previous_period: bool = False
    ) -> str:
        """Return the given path with the period specifier appended to it, appended to the data dir."""
        return self.with_period_specifier(self.from_data_dir(path), previous_period)

    def split_path(self, split: str) -> str:
        """Get the path to a split."""
        y_split = Y_SPLIT_TEMPLATE.substitute(split=split)
        return self.from_data_dir_with_period_specifier(y_split)

    def load_split(self, split: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Load a split of the data."""
        return self.get_from_ipfs(
            getattr(self.synchronized_data, f"{split}_hash"),
            self.split_path(split),
            multiple=True,
            filetype=ExtendedSupportedFiletype.CSV,
        )


class FetchBehaviour(
    APYEstimationBaseBehaviour, SubgraphsMixin
):  # pylint: disable=too-many-ancestors
    """Observe historical data."""

    behaviour_id = "fetch"
    matching_round = CollectHistoryRound
    batch = False

    @dataclass
    class Progress:
        """A class to keep track of the download progress."""

        timestamps_iterator: Optional[Iterator[int]] = None
        current_timestamp: Optional[int] = None
        dex_names_iterator: Optional[Iterator[str]] = None
        current_dex_name: Optional[str] = None
        n_fetched = 0
        call_failed = False
        initialized = False

        @property
        def can_continue(self) -> bool:
            """Get if the fetching can continue."""
            return all(
                current is not None
                for current in (
                    self.current_timestamp,
                    self.current_dex_name,
                )
            )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Behaviour."""
        super().__init__(**kwargs)
        SubgraphsMixin.__init__(self)
        self._save_path = ""
        self._progress = self.Progress()
        self._progress.dex_names_iterator = iter(self.params.pair_ids)
        self._pairs_hist: ResponseItemType = []
        self._hist_hash: Optional[str] = None
        self._unit = ""
        self._target_per_pool = 0
        self._target = 0
        self._pairs_exist = False

    @property
    def current_pair_ids(self) -> List[str]:
        """Get the current DEX's pair ids."""
        if self._progress.initialized:
            current_dex_name = cast(str, self._progress.current_dex_name)
            return self.params.pair_ids[current_dex_name]
        return []

    @property
    def current_dex(self) -> Union[DEXSubgraph, ApiSpecs]:
        """Get the current DEX subgraph."""
        if self._progress.initialized:
            current_dex_name = cast(str, self._progress.current_dex_name)
            return self.get_subgraph(current_dex_name)
        return self.get_subgraph("default")

    @property
    def current_chain(self) -> ApiSpecs:
        """Get the current block subgraph."""
        return self.get_subgraph(self.current_dex.chain_subgraph_name)

    @property
    def currently_downloaded(self) -> int:
        """Get the number of the currently downloaded unit, for the current pool."""
        if self._progress.initialized:
            return int(
                (len(self._pairs_hist) - self._progress.n_fetched)
                / len(self.current_pair_ids)
            )
        return 0

    @property
    def total_downloaded(self) -> int:
        """Get the number of the downloaded unit, in total."""
        return len(self._pairs_hist)

    @property
    def retries_exceeded(self) -> bool:
        """If the retries have been exceeded for any subgraph."""
        return any(
            subgraph.is_retries_exceeded() for subgraph in self.utilized_subgraphs
        )

    def setup(self) -> None:
        """Set the behaviour up."""
        if self.params.end is None or self.batch:
            last_timestamp = cast(
                SharedState, self.context.state
            ).round_sequence.abci_app.last_timestamp
            self.params.end = int(calendar.timegm(last_timestamp.timetuple()))

        self._unit = sec_to_unit(self.params.interval)
        self._target_per_pool = int(
            unit_amount_from_sec(self.params.end - self.params.start, self._unit)
        )
        n_ids = sum(
            (len(dex_pair_ids) for dex_pair_ids in self.params.pair_ids.values())
        )
        self._target = self._target_per_pool * n_ids

        filename = (
            HISTORICAL_DATA_BATCH_PATH_TEMPLATE.substitute(
                batch_number=self.params.end,
                period_count=self.synchronized_data.period_count,
            )
            if self.batch
            else HISTORICAL_DATA_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            )
        )
        self._save_path = self.from_data_dir(filename)

    def _check_given_pairs(self) -> Generator[None, None, None]:
        """Check if the pairs that the user placed in the config file exist on the corresponding subgraphs."""
        existing_pairs: List[str] = []
        given_pairs = []
        for dex_name, pair_ids in self.params.pair_ids.items():
            given_pairs.extend(pair_ids)
            dex = self.get_subgraph(dex_name)
            res_raw = yield from self.get_http_response(
                content=existing_pairs_q(pair_ids),
                **dex.get_spec(),
            )
            res = dex.process_response(res_raw)

            pairs = yield from self._handle_response(
                res,
                res_context="pool ids",
                keys=("pairs",),
                subgraph=dex,
            )

            if pairs is not None:
                pairs = cast(List[Dict[str, str]], pairs)
                existing_pairs.extend(pair["id"] for pair in pairs)

        non_existing_pairs = set(given_pairs) - set(existing_pairs)
        if non_existing_pairs:
            if not self._progress.call_failed:
                self.context.logger.error(
                    f"The given pair(s) {non_existing_pairs} do not exist at the corresponding subgraph(s)!"
                )
            return

        self._pairs_exist = True

    def _reset_timestamps_iterator(self) -> None:
        """Reset the timestamps iterator."""
        # end is set in the `setup` method and therefore cannot be `None` at this point
        end = cast(int, self.params.end)

        if self.batch:
            self._progress.timestamps_iterator = iter((end,))
        else:
            self._progress.timestamps_iterator = gen_unix_timestamps(
                self.params.start, self.params.interval, end
            )

    def _set_current_progress(self) -> None:
        """Set the progress for the current timestep in the async act."""
        if not self._progress.call_failed:
            if (
                self.currently_downloaded == 0
                or self.currently_downloaded == self._target_per_pool
                or self.batch
            ):
                self._progress.current_dex_name = next(
                    cast(Iterator[str], self._progress.dex_names_iterator),
                    None,
                )
                self._reset_timestamps_iterator()
                self._progress.n_fetched = len(self._pairs_hist)

            self._progress.current_timestamp = next(
                cast(Iterator[int], self._progress.timestamps_iterator),
                None,
            )

        if self.retries_exceeded:
            # We cannot continue if the data were not fetched.
            # It is going to make the agent fail in the next behaviour while looking for the historical data file.
            self.context.logger.error(
                "Retries were exceeded while downloading the historical data!"
            )
            # This will result in using only the part of the data downloaded so far.
            self._progress.current_timestamp = None
            self._progress.current_dex_name = None
            # manually call clean-up, as it is not called by the framework if a `StopIteration` is not raised
            self.clean_up()

        self._progress.initialized = True
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

            self._progress.call_failed = True
            subgraph.increment_retries()
            if sleep_on_fail:
                yield from self.sleep(self.params.sleep_time)
            return None

        value = res[keys[0]]
        if len(keys) > 1:
            for key in keys[1:]:
                value = value[key]

        self.context.logger.info(f"Retrieved {res_context}: {value}.")
        self._progress.call_failed = False
        subgraph.reset_retries()
        return value

    def _fetch_block(
        self, number: Optional[int] = None
    ) -> Generator[None, None, Optional[Dict[str, int]]]:
        """Fetch block."""
        if number is not None:
            query = block_from_number_q(number)
        else:
            query = (
                latest_block_q()
                if self.batch
                else block_from_timestamp_q(cast(int, self._progress.current_timestamp))
            )

        res_raw = yield from self.get_http_response(
            **self.current_chain.get_spec(),
            content=query,
        )
        res = self.current_chain.process_response(res_raw)

        fetched_block = yield from self._handle_response(
            res,
            res_context="block",
            keys=("blocks", 0),
            subgraph=self.current_chain,
        )

        return fetched_block

    def _fetch_eth_price(
        self, block: Dict[str, int]
    ) -> Generator[None, None, Tuple[HttpMessage, Optional[float]]]:
        """Fetch ETH price for block."""
        res_raw = yield from self.get_http_response(
            content=eth_price_usd_q(
                self.current_dex.bundle_id,
                block["number"],
            ),
            **self.current_dex.get_spec(),
        )
        res = self.current_dex.process_response(res_raw)

        eth_price = yield from self._handle_response(
            res,
            res_context=f"ETH price for block {block}",
            keys=("bundles", 0, "ethPrice"),
            subgraph=self.current_dex,
            sleep_on_fail=False,
        )

        return res_raw, eth_price

    def _check_non_indexed_block(
        self, res_raw: HttpMessage
    ) -> Generator[None, None, Optional[Tuple[Dict[str, int], float]]]:
        """Check if we received a non-indexed block error and try to get the ETH price for the latest indexed block."""
        res = self.current_dex.process_non_indexed_error(res_raw)
        latest_indexed_block_error = yield from self._handle_response(
            res,
            res_context="indexing error that will be attempted to be handled",
            keys=(0, "message"),
            subgraph=self.current_dex,
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
        self,
        block: Dict[str, int],
    ) -> Generator[None, None, Optional[ResponseItemType]]:
        """Fetch pool data for block."""
        res_raw = yield from self.get_http_response(
            content=pairs_q(block["number"], self.current_pair_ids),
            **self.current_dex.get_spec(),
        )
        res = self.current_dex.process_response(res_raw)

        pairs = yield from self._handle_response(
            res,
            res_context=f"pool data for block {block}",
            keys=("pairs",),
            subgraph=self.current_dex,
        )

        return pairs

    def _fetch_batch(self) -> Generator[None, None, None]:
        """Fetch a single batch of the historical data, for the current DEX."""
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
            pairs[i]["forTimestamp"] = str(self._progress.current_timestamp)
            pairs[i]["blockNumber"] = str(block["number"])
            pairs[i]["blockTimestamp"] = str(block["timestamp"])
            pairs[i]["ethPrice"] = str(eth_price)

        self._pairs_hist.extend(pairs)

        if not self.batch:
            self.context.logger.info(
                f"Fetched {self._unit} {self.currently_downloaded}/{self._target_per_pool} "
                f"from {self._progress.current_dex_name}."
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
        if not self._progress.initialized:
            yield from self._check_given_pairs()
            if self._progress.call_failed and not self.retries_exceeded:
                return

        if self._pairs_exist:
            self._set_current_progress()

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            if self._progress.can_continue:
                yield from self._fetch_batch()
                return

            if self.total_downloaded == 0:
                self.context.logger.error("Could not download any historical data!")
                self._hist_hash = ""

            if (
                self.total_downloaded > 0
                and self.total_downloaded != self._target
                and not self.batch
            ):
                # Here, we continue without having all the pairs downloaded, because of a network issue.
                self.context.logger.warning(
                    "Will continue with partially downloaded historical data!"
                )

            if self.total_downloaded > 0:
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
        for subgraph in self.utilized_subgraphs:
            subgraph.reset_retries()


class FetchBatchBehaviour(FetchBehaviour):  # pylint: disable=too-many-ancestors
    """Observe the latest batch of historical data."""

    behaviour_id = "fetch_batch"
    matching_round = CollectLatestHistoryBatchRound
    batch = True


class TransformBehaviour(
    APYEstimationBaseBehaviour
):  # pylint: disable=too-many-ancestors
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
            filename=HISTORICAL_DATA_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            ),
            filetype=SupportedFiletype.JSON,
        )

        self._transformed_history_save_path = self.from_data_dir(
            TRANSFORMED_HISTORICAL_DATA_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            )
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
                filetype=ExtendedSupportedFiletype.CSV,
            )

            # Get the latest observation for each pool id.
            latest_observations = transformed_history.groupby("id").last().reset_index()
            # Send the latest observations to IPFS and get the hash.
            latest_observations_save_path = self.from_data_dir(
                LATEST_OBSERVATIONS_PATH_TEMPLATE.substitute(
                    period_count=self.synchronized_data.period_count
                )
            )
            self._latest_observations_hist_hash = self.send_to_ipfs(
                latest_observations_save_path,
                latest_observations,
                filetype=ExtendedSupportedFiletype.CSV,
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
            filename=TRANSFORMED_HISTORICAL_DATA_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            ),
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
                split_hash = self.send_to_ipfs(
                    self.split_path(split_name),
                    split,
                    multiple=True,
                    filetype=ExtendedSupportedFiletype.CSV,
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
                filename=LATEST_OBSERVATIONS_PATH_TEMPLATE.substitute(
                    period_count=self.synchronized_data.period_count - 1
                ),
                custom_loader=load_hist,
            ),
            self.get_from_ipfs(
                self.synchronized_data.batch_hash,
                self.context.data_dir,
                filename=HISTORICAL_DATA_BATCH_PATH_TEMPLATE.substitute(
                    batch_number=self.params.end,
                    period_count=self.synchronized_data.period_count,
                ),
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
            LATEST_OBSERVATIONS_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            ),
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
                filetype=ExtendedSupportedFiletype.CSV,
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
            self._best_params_hash = self.send_to_ipfs(
                self.from_data_dir_with_period_specifier(BEST_PARAMS_PATH),
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
        self._best_params = self.get_from_ipfs(
            self.synchronized_data.params_hash,
            self.from_data_dir_with_period_specifier(BEST_PARAMS_PATH),
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

            forecaster_save_path = (
                FULLY_TRAINED_FORECASTERS_PATH
                if self.synchronized_data.full_training
                else FORECASTERS_PATH
            )
            forecaster_save_path = self.from_data_dir_with_period_specifier(
                forecaster_save_path
            )

            # Send the file to IPFS and get its hash.
            self._models_hash = self.send_to_ipfs(
                forecaster_save_path,
                forecasters,
                multiple=True,
                filetype=ExtendedSupportedFiletype.PM_PIPELINE,
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

        models_path = self.from_data_dir_with_period_specifier(FORECASTERS_PATH)

        self._forecasters = self.get_from_ipfs(
            self.synchronized_data.models_hash,
            models_path,
            multiple=True,
            filetype=ExtendedSupportedFiletype.PM_PIPELINE,
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

            # Send the file to IPFS and get its hash.
            self._report_hash = self.send_to_ipfs(
                self.from_data_dir_with_period_specifier(REPORTS_PATH),
                report,
                multiple=True,
                filetype=SupportedFiletype.JSON,
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
        self._forecasters: Optional[PoolIdToForecasterType] = None
        self._models_hash: Optional[str] = None

    def setup(self) -> None:
        """Setup behaviour."""
        # Load data batch.
        self._y = self.get_from_ipfs(
            self.synchronized_data.latest_observation_hist_hash,
            self.context.data_dir,
            filename=LATEST_OBSERVATIONS_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            ),
            filetype=ExtendedSupportedFiletype.CSV,
        )

        # Load forecasters.
        self._forecasters = self.get_from_ipfs(
            self.synchronized_data.models_hash,
            self.from_data_dir_with_period_specifier(
                FULLY_TRAINED_FORECASTERS_PATH, previous_period=True
            ),
            multiple=True,
            filetype=ExtendedSupportedFiletype.PM_PIPELINE,
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
                self.from_data_dir_with_period_specifier(
                    FULLY_TRAINED_FORECASTERS_PATH
                ),
                self._forecasters,
                multiple=True,
                filetype=ExtendedSupportedFiletype.PM_PIPELINE,
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
        self._forecasters = self.get_from_ipfs(
            self.synchronized_data.models_hash,
            self.from_data_dir_with_period_specifier(FULLY_TRAINED_FORECASTERS_PATH),
            multiple=True,
            filetype=ExtendedSupportedFiletype.PM_PIPELINE,
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
            estimates = estimates.round(self.params.decimals)
            self.context.logger.info(
                "Estimates have been received:\n" f"{estimates.to_string()}"
            )
            self.context.logger.info("Estimates have been received.")

            # Send the file to IPFS and get its hash.
            self._estimations_hash = self.send_to_ipfs(
                self.from_data_dir(
                    ESTIMATIONS_PATH_TEMPLATE.substitute(
                        period_count=self.synchronized_data.period_count
                    )
                ),
                estimates,
                filetype=ExtendedSupportedFiletype.CSV,
            )

        payload = EstimatePayload(self.context.agent_address, self._estimations_hash)

        # Finish behaviour.
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class BaseResetBehaviour(APYEstimationBaseBehaviour):
    """Reset behaviour."""

    start_fresh = False

    def _get_finalized_estimates(self) -> Optional[pd.DataFrame]:
        """Fetch the finalized estimates from IPFS and log the result."""
        # Load estimations.
        estimations = self.get_from_ipfs(
            self.synchronized_data.estimates_hash,
            self.context.data_dir,
            filename=ESTIMATIONS_PATH_TEMPLATE.substitute(
                period_count=self.synchronized_data.period_count
            ),
            filetype=ExtendedSupportedFiletype.CSV,
        )
        if estimations is not None:
            self.context.logger.info(f"Finalized estimates: {estimations.to_string()}.")
        else:
            self.context.logger.error(
                "There was an error while trying to fetch and load the estimations from IPFS!"
            )

        return estimations

    @staticmethod
    def _pack_for_server(
        period_count: int,
        agent_address: str,
        n_participants: int,
        estimations: str,
        total_estimations: int,
    ) -> bytes:
        """Package server data for signing."""
        return b"".join(
            [
                period_count.to_bytes(32, "big"),
                str(agent_address).zfill(32).encode("utf-8"),
                n_participants.to_bytes(32, "big"),
                total_estimations.to_bytes(32, "big"),
                # we cannot know the size of the estimations, since it depends on the number of pools
                estimations.encode("utf-8"),
            ]
        )

    def _send_to_server(self, estimations: pd.DataFrame) -> Generator:
        """Send the estimations to the server."""
        self.context.logger.info("Attempting broadcast...")

        # Adding timestamp on server side when received. Period and agent_address are used as `primary key`.
        data_for_server = {
            "period_count": self.synchronized_data.period_count,
            "agent_address": self.context.agent_address,
            "n_participants": len(self.synchronized_data.participant_to_estimate),
            "estimations": estimations.to_json(),
            "total_estimations": self.synchronized_data.n_estimations,
        }

        # pack data
        package = self._pack_for_server(**data_for_server)
        data_for_server["package"] = package.hex()

        # get signature
        signature = yield from self.get_signature(package, is_deprecated_mode=True)
        data_for_server["signature"] = signature
        self.context.logger.info(f"Package signature: {signature}")

        message = str(data_for_server).encode("utf-8")
        server_api_specs = self.context.server_api.get_spec()
        raw_response = yield from self.get_http_response(
            content=message,
            **server_api_specs,
        )

        response = self.context.server_api.process_response(raw_response)
        self.context.logger.info(f"Broadcast response: {response}")

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
        estimations = None
        if self.synchronized_data.is_most_voted_estimate_set:
            estimations = self._get_finalized_estimates()
        else:
            self.context.logger.error("Finalized estimates not available!")

        if self.params.is_broadcasting_to_server and estimations is not None:
            yield from self._send_to_server(estimations)

        log_msg = (
            "Resetting to create a fresh forecasting model"
            if self.start_fresh
            else "Estimation will happen again"
        )
        log_msg += f" in {self.params.observation_interval} seconds."
        self.context.logger.info(log_msg)

        yield from self.sleep(self.params.observation_interval)
        self.context.benchmark_tool.save()

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
    start_fresh = True


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
