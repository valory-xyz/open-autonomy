# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

# nosec

"""Query templates."""

FIND_BY_PACKAGE_HASH = """
query getUnit {{
  units(where:{{packageHash:"{package_hash}"}}){{
    tokenId
    packageHash
    publicId
  }}
}}
"""

FIND_BY_PUBLIC_ID = """
query getUnit {{
  units(where:{{publicId: "{public_id}",packageType:{package_type}}}){{
    tokenId
    packageHash
    publicId
  }}
}}
"""

# The bandit check fails here and adding nosec tag does not work because
# the black formatter puts the nosec tag to the end of the declaration
# so I declared the template as singleton and deconstructed the tuple to
# constant value

(FIND_BY_TOKEN_ID,) = (  # nosec
    """
query getUnit {{
  units(where:{{tokenId: "{token_id}",packageType:{package_type}}}){{
    tokenId
    packageHash
    publicId
  }}
}}
""",
)
