## Communication
This diagram shows the communication flow between the AEAs and their environment.

<div class="mermaid">
    sequenceDiagram
        activate KeeperAgent
        activate ConsensusEngine
        activate OtherAgents
        activate Blockchain
        activate PriceAPI
        activate RandomnessSource

        Note left of KeeperAgent: HealthCheck

        KeeperAgent->>ConsensusEngine: get_status
        ConsensusEngine-->>KeeperAgent: ok_response
        OtherAgents->>ConsensusEngine: get_status
        ConsensusEngine-->>OtherAgents: ok_response

        Note left of KeeperAgent: Initialization

        ConsensusEngine-->>KeeperAgent: ready_signal
        ConsensusEngine-->>OtherAgents: ready_signal

        Note left of KeeperAgent: Registration

        KeeperAgent->>ConsensusEngine: register_service
        KeeperAgent->>ConsensusEngine: search_agents
        OtherAgents->>ConsensusEngine: register_service
        OtherAgents->>ConsensusEngine: search_agents
        ConsensusEngine-->>KeeperAgent: list_of_agents
        ConsensusEngine-->>OtherAgents: list_of_agents

        Note left of KeeperAgent: Randomness

        KeeperAgent->>RandomnessSource: get_randomness
        RandomnessSource-->>KeeperAgent: randomness
        OtherAgents->>RandomnessSource: get_randomness
        RandomnessSource-->>OtherAgents: randomness

        Note left of KeeperAgent: KeeperSelection

        KeeperAgent->>ConsensusEngine: vote_keeper
        OtherAgents->>ConsensusEngine: vote_keeper
        ConsensusEngine-->>KeeperAgent: keeper
        ConsensusEngine-->>OtherAgents: keeper

        Note left of KeeperAgent: DeploySafe

        KeeperAgent->>Blockchain: deploy_safe_contract
        Blockchain-->>KeeperAgent: contract_adress
        KeeperAgent->>ConsensusEngine: contract_adress

        Note left of KeeperAgent: ValidateSafe

        KeeperAgent->>ConsensusEngine: validate
        OtherAgents->>ConsensusEngine: validate
        ConsensusEngine-->>KeeperAgent: validated
        ConsensusEngine-->>OtherAgents: validated

        Note left of KeeperAgent: DeployOracle

        KeeperAgent->>Blockchain: deploy_oracle_contract
        Blockchain-->>KeeperAgent: contract_adress
        KeeperAgent->>ConsensusEngine: contract_adress

        Note left of KeeperAgent: ValidateOracle

        KeeperAgent->>ConsensusEngine: validate
        OtherAgents->>ConsensusEngine: validate
        ConsensusEngine-->>KeeperAgent: validated
        ConsensusEngine-->>OtherAgents: validated

        Note left of KeeperAgent: Observation

        KeeperAgent->>PriceAPI: observe_price
        PriceAPI-->>KeeperAgent:price_observation
        OtherAgents->>PriceAPI: observe_price
        PriceAPI-->>OtherAgents: price_observation

        KeeperAgent->>ConsensusEngine: collect_observations
        ConsensusEngine-->>KeeperAgent: observations
        OtherAgents->>ConsensusEngine: collect_observations
        ConsensusEngine-->>OtherAgents: observations

        Note left of KeeperAgent: Estimation

        KeeperAgent->>KeeperAgent: estimate_price
        OtherAgents->>OtherAgents: estimate_price

        Note left of KeeperAgent: TransactionHash

        KeeperAgent->>ConsensusEngine: transaction_hash

        Note left of KeeperAgent: Signature

        ConsensusEngine-->>OtherAgents: collect_tx
        KeeperAgent->>ConsensusEngine: tx_signature
        OtherAgents->>ConsensusEngine: tx_signature
        ConsensusEngine-->>KeeperAgent: collect_signatures
        ConsensusEngine-->>OtherAgents: collect_signatures

        Note left of KeeperAgent: Finalization

        KeeperAgent->>Blockchain: final_tx
        Blockchain-->>KeeperAgent: final_tx_hash
        KeeperAgent->>ConsensusEngine: final_tx_hash
        ConsensusEngine-->>OtherAgents: final_tx_hash

        Note left of KeeperAgent: ValidateTx

        KeeperAgent->>ConsensusEngine: validate
        OtherAgents->>ConsensusEngine: validate
        ConsensusEngine-->>KeeperAgent: validated
        ConsensusEngine-->>OtherAgents: validated

        Note left of KeeperAgent: End

        KeeperAgent->>KeeperAgent: end
        OtherAgents->>OtherAgents: end

        deactivate KeeperAgent
        deactivate ConsensusEngine
        deactivate OtherAgents
        deactivate Blockchain
        deactivate PriceAPI
        deactivate RandomnessSource
</div>