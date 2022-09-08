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

"""This module contains the constants for the APY estimation skill."""


from string import Template


_BATCH = "batch_${batch_number}"
_PERIOD_SPECIFIER = "period_${period_count}"
_HISTORICAL_DATA = "historical_data"

# paths_without_suffixes
_HISTORICAL_DATA_PATH = "_".join((_HISTORICAL_DATA, _PERIOD_SPECIFIER))
_HISTORICAL_DATA_BATCH_PATH = "_".join((_HISTORICAL_DATA, _BATCH, _PERIOD_SPECIFIER))
_TRANSFORMED_HISTORICAL_DATA_PATH = "_".join(
    ("transformed", _HISTORICAL_DATA, _PERIOD_SPECIFIER)
)
_LATEST_OBSERVATIONS_PATH = "_".join(("latest_observations", _PERIOD_SPECIFIER))
_ESTIMATIONS_PATH = "_".join(("estimations", _PERIOD_SPECIFIER))

# suffixes
_JSON_SUFFIX = ".json"
_CSV_SUFFIX = ".csv"

# filepaths with suffixes
_HISTORICAL_DATA_PATH += _JSON_SUFFIX
_HISTORICAL_DATA_BATCH_PATH += _JSON_SUFFIX
_TRANSFORMED_HISTORICAL_DATA_PATH += _CSV_SUFFIX
_LATEST_OBSERVATIONS_PATH += _CSV_SUFFIX
_ESTIMATIONS_PATH += _CSV_SUFFIX

# templates
Y_SPLIT_TEMPLATE = Template("y_${split}")
PERIOD_SPECIFIER_TEMPLATE = Template(_PERIOD_SPECIFIER)

# final filepath templates
HISTORICAL_DATA_PATH_TEMPLATE = Template(_HISTORICAL_DATA_PATH)
HISTORICAL_DATA_BATCH_PATH_TEMPLATE = Template(_HISTORICAL_DATA_BATCH_PATH)
TRANSFORMED_HISTORICAL_DATA_PATH_TEMPLATE = Template(_TRANSFORMED_HISTORICAL_DATA_PATH)
LATEST_OBSERVATIONS_PATH_TEMPLATE = Template(_LATEST_OBSERVATIONS_PATH)
ESTIMATIONS_PATH_TEMPLATE = Template(_ESTIMATIONS_PATH)

# paths for folders
BEST_PARAMS_PATH = "best_params"
FORECASTERS_PATH = "forecasters"
FULLY_TRAINED_FORECASTERS_PATH = "_".join(("fully_trained_", FORECASTERS_PATH))
REPORTS_PATH = "reports"
