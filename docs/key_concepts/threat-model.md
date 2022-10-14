It is important to note that autonomous services (and hence agent services) do not need to store the history of the common service state permanently. This implies that agent services may be internally using blockchain-like technology, but they never implement a standard L1/L2 layer.

Autonomous services work under the following threat model:

- A service is managed by a service owner, who is in charge of managing the service life cycle (e.g. sets it up and can shut it down)

- A service is run by a set of operators, each running at least one agent instance, for a total of n agent instances

- Every pair of agent instances in the service can securely and independently communicate

- A majority of the n agent instances run the agent code defined by the service (typically at most ⅓ of the instances are allowed to be malicious for the service to be guaranteed to run)

- A malicious agent instance can deviate arbitrarily from the code that is supposed to run

- A service is registered in a L1/L2 blockchain from which the economic security of the service is bootstrapped

- Every operator must lock a deposit for each agent instance they own  in the L1/L2 blockchain where the service was registered

- Agents can punish each other's misbehavior by submitting fraud proofs to the underlying chain, causing slashing of the deposit of the malicious instance

- The service owner locks a deposit equal to the largest deposit requested from the agent instances. This is used to incentivise the service owner to release the agents deposits at the end of the lifetime of the service

An autonomous (or agent) service is decentralized by virtue of minimizing the trust placed on individual agent instances. Although a service owner could potentially be penalized for misbehavior, they are assumed to act honestly.
