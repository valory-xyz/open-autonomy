
## EIP-1559 Transactions

With EIP-1559 transaction pricing has changed. Previously, one simply had to set `gasPrice`, now two new pricing parameters have to be set (`maxFeePerGas` and `maxPriorityFeePerGas`):

- The Base Fee, which is determined by the network itself. And is subsequently burned. (The Base Fee targets 50% full blocks and is based upon the contents of the most recent confirmed block. Depending on how full that new block is, the Base Fee is automatically increased or decreased.)
- A Max Priority Fee, which is optional, determined by the user, and is paid directly to miners. (While the Max Priority Fee is technically optional, at the moment most network participants estimate that transactions generally require a minimum 2.0 GWEI tip to be candidates for inclusion.)
- The Max Fee Per Gas, which is the absolute maximum you are willing to pay per unit of gas to get your transaction included in a block. For brevity and clarity, we will refer to this as the Max Fee.  (if the Base Fee plus the Max Priority Fee exceeds the Max Fee (see below), the Max Priority Fee will be reduced in order to maintain the upper bound of the Max Fee. E.g. heuristic: Max Fee = (2 * Base Fee) + Max Priority Fee. Doubling the Base Fee when calculating  the Max Fee ensures that your transaction will remain marketable for six consecutive 100% full blocks. )

Transactions that include these new fields are known as Type 2, while legacy transactions that carry the original Gas Price field remain supported and known as Type 0.

EIP-1559 does not bring changes to the Gas Limit, the maximum amount of gas the transaction is authorized to consume.

Sources: https://www.blocknative.com/blog/eip-1559-fees


## Delegate call vs call

Delegate call can be difficult to wrap your head around, but think of it this way: a delegate call means "load the code from this address and run it". This means that, when you create the Safe tx with operation=delegatecall, you are telling the Safe to get the code from the contract whose address is provided and execute it.


## Debugging using Tenderly:

[Tenderly](https://tenderly.co/) is a *"comprehensive Ethereum Developer Platform for real-time monitoring, alerting, debugging, and simulating Smart Contracts"*. When debugging transactions and contract calls, it can be useful to help us understand what's going on with our execution. [This guide](http://blog.tenderly.co/level-up-your-smart-contract-productivity-using-hardhat-and-tenderly/) contains a more exhaustive explanation on Tenderly, but for the basics:

- Create a Tenderly account and project.

- Set your Tenderly username and project name at `tenderly.yaml` (`exports/ganache/project_slug`) and at your `hardhat.config.js` module exports:

    ```
    tenderly: {
      username: "username",
      project: "projectname"
    }
    ```

- Login to Tenderly using your username and password or an access token:
    ```
    tenderly login
    ```

- Run your Hardhat deployment and export your transactions with:
    ```
    tenderly export <transaction_hash>
    ```
- You'll see a link to your Tenderly dashboard where you can inspect the full transaction stack trace.
- During testing, you will need to pause Hardhat's execution before it ends to export the transaction.
- Optionally, there's the possibility of pushing your contract's source to verify and debug it. More on that [here](http://blog.tenderly.co/level-up-your-smart-contract-productivity-using-hardhat-and-tenderly/).
