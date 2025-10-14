## Communication
This diagram shows the communication flow between the AEAs and their environment.

<div class="mermaid">
    sequenceDiagram
        activate KeeperAgentInstance
        activate ConsensusEngine
        activate OtherAgentInstances
        activate Blockchain
        activate PriceAPI
        activate RandomnessSource

        Note left of KeeperAgentInstance: HealthCheck

        KeeperAgentInstance->>ConsensusEngine: get_status
        ConsensusEngine-->>KeeperAgentInstance: ok_response
        OtherAgentInstances->>ConsensusEngine: get_status
        ConsensusEngine-->>OtherAgentInstances: ok_response

        Note left of KeeperAgentInstance: Initialization

        ConsensusEngine-->>KeeperAgentInstance: ready_signal
        ConsensusEngine-->>OtherAgentInstances: ready_signal

        Note left of KeeperAgentInstance: Registration

        KeeperAgentInstance->>ConsensusEngine: register_service
        KeeperAgentInstance->>ConsensusEngine: search_agents
        OtherAgentInstances->>ConsensusEngine: register_service
        OtherAgentInstances->>ConsensusEngine: search_agents
        ConsensusEngine-->>KeeperAgentInstance: list_of_agents
        ConsensusEngine-->>OtherAgentInstances: list_of_agents

        Note left of KeeperAgentInstance: Randomness

        KeeperAgentInstance->>RandomnessSource: get_randomness
        RandomnessSource-->>KeeperAgentInstance: randomness
        OtherAgentInstances->>RandomnessSource: get_randomness
        RandomnessSource-->>OtherAgentInstances: randomness

        Note left of KeeperAgentInstance: KeeperSelection

        KeeperAgentInstance->>ConsensusEngine: vote_keeper
        OtherAgentInstances->>ConsensusEngine: vote_keeper
        ConsensusEngine-->>KeeperAgentInstance: keeper
        ConsensusEngine-->>OtherAgentInstances: keeper

        Note left of KeeperAgentInstance: DeploySafe

        KeeperAgentInstance->>Blockchain: deploy_safe_contract
        Blockchain-->>KeeperAgentInstance: contract_adress
        KeeperAgentInstance->>ConsensusEngine: contract_adress

        Note left of KeeperAgentInstance: ValidateSafe

        KeeperAgentInstance->>ConsensusEngine: validate
        OtherAgentInstances->>ConsensusEngine: validate
        ConsensusEngine-->>KeeperAgentInstance: validated
        ConsensusEngine-->>OtherAgentInstances: validated

        Note left of KeeperAgentInstance: DeployOracle

        KeeperAgentInstance->>Blockchain: deploy_oracle_contract
        Blockchain-->>KeeperAgentInstance: contract_adress
        KeeperAgentInstance->>ConsensusEngine: contract_adress

        Note left of KeeperAgentInstance: ValidateOracle

        KeeperAgentInstance->>ConsensusEngine: validate
        OtherAgentInstances->>ConsensusEngine: validate
        ConsensusEngine-->>KeeperAgentInstance: validated
        ConsensusEngine-->>OtherAgentInstances: validated

        Note left of KeeperAgentInstance: Observation

        KeeperAgentInstance->>PriceAPI: observe_price
        PriceAPI-->>KeeperAgentInstance:price_observation
        OtherAgentInstances->>PriceAPI: observe_price
        PriceAPI-->>OtherAgentInstances: price_observation

        KeeperAgentInstance->>ConsensusEngine: collect_observations
        ConsensusEngine-->>KeeperAgentInstance: observations
        OtherAgentInstances->>ConsensusEngine: collect_observations
        ConsensusEngine-->>OtherAgentInstances: observations

        Note left of KeeperAgentInstance: Estimation

        KeeperAgentInstance->>KeeperAgentInstance: estimate_price
        OtherAgentInstances->>OtherAgentInstances: estimate_price

        Note left of KeeperAgentInstance: TransactionHash

        KeeperAgentInstance->>ConsensusEngine: transaction_hash

        Note left of KeeperAgentInstance: Signature

        ConsensusEngine-->>OtherAgentInstances: collect_tx
        KeeperAgentInstance->>ConsensusEngine: tx_signature
        OtherAgentInstances->>ConsensusEngine: tx_signature
        ConsensusEngine-->>KeeperAgentInstance: collect_signatures
        ConsensusEngine-->>OtherAgentInstances: collect_signatures

        Note left of KeeperAgentInstance: Finalization

        KeeperAgentInstance->>Blockchain: final_tx
        Blockchain-->>KeeperAgentInstance: final_tx_hash
        KeeperAgentInstance->>ConsensusEngine: final_tx_hash
        ConsensusEngine-->>OtherAgentInstances: final_tx_hash

        Note left of KeeperAgentInstance: ValidateTx

        KeeperAgentInstance->>ConsensusEngine: validate
        OtherAgentInstances->>ConsensusEngine: validate
        ConsensusEngine-->>KeeperAgentInstance: validated
        ConsensusEngine-->>OtherAgentInstances: validated

        Note left of KeeperAgentInstance: End

        KeeperAgentInstance->>KeeperAgentInstance: end
        OtherAgentInstances->>OtherAgentInstances: end

        deactivate KeeperAgentInstance
        deactivate ConsensusEngine
        deactivate OtherAgentInstances
        deactivate Blockchain
        deactivate PriceAPI
        deactivate RandomnessSource
</div>