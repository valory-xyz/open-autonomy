# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright {{cookiecutter.year}} Valory AG
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

"""This module contains the class to connect to a ERC20 contract."""
import logging
from typing import Any, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_erc20:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

# pylint: disable=too-many-arguments,invalid-name
class {{cookiecutter.class_name}}(Contract):
    """The {{cookiecutter.contract_name}} contract."""

    contract_id = PUBLIC_ID

{% for function, inputs in cookiecutter.write_functions|dictsort %}
    @classmethod
    def {{function}}(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        {% for input_name, input_type in inputs.items() -%}
        {% if input_name in ("from", "to") -%}
        {{input_name}}_address: {{input_type}},
        {% else -%}
        {{input_name}}: {{input_type}},
        {% endif -%}
        {% endfor -%}
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Doctring for the '{{function}}' function."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance=contract_instance,
            method_name="{{function}}",
            method_args={
                {%- for input_name, input_type in inputs.items() %}
                {%- if input_name in ("from", "to") %}
                "{{input_name}}": {{input_name}}_address,
                {%- else %}
                "{{input_name}}": {{input_name}},
                {%- endif -%}
                {%- endfor %}
            },
            tx_args=kwargs,
        )
{% endfor -%}

{% for function, inputs in cookiecutter.read_functions|dictsort %}
    @classmethod
    def {{function}}(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        {%- for input_name, input_type in inputs|dictsort %}
        {{input_name}}: {{input_type}},
        {%- endfor +%}
    ) -> Optional[JSONLike]:
        """Doctring for the '{{function}}' function."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="{{function}}",
            {%- for input_name, input_type in inputs|dictsort %}
            {{input_name}}={{input_name}},
            {%- endfor %}
        )
{% endfor -%}