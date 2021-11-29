from tests.test_contracts.test_uniswap_v2_router_02.test_contract import BaseContractTestHardHatAMMNet

import time

DEFAULT_GAS = 1000000
DEFAULT_GAS_PRICE = 1000000


class TestHardhat(BaseContractTestHardHatAMMNet):
    """Test liquidity pool behaviours in a Hardhat environment."""

    def test_swap(self):
        """Test a swap tx: WETH for token A."""

        amount_in = 10
        amount_out_min = 1

        # Prepare the tx
        result = self.contract.swap_exact_tokens_for_tokens(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            sender_address=self.account_1_address,
            gas=DEFAULT_GAS,
            gas_price=DEFAULT_GAS_PRICE,
            amount_in=amount_in,
            amount_out_min=amount_out_min,
            path=[
                self.weth_address,
                self.tokenA_address,
            ],
            to_address=self.account_1_address,
            deadline=int(time.time()) + 300,  # 5 min into the future
        )

        # Send the tx

        # Verify the tx
        assert type(result) == dict