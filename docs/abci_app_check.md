# ABCI Application specification checks

Check, Generate or Compare the implementation and specification of an `ABCIApp`.

## Checking the consistency of an ABCI App implementation

Within the [`scripts/`](../scripts) folder one can find a tool that allows a developer to check whether the necessary 
requirements for a properly defined Finite State Machine (FSM) are met. It furthermore allows a use to derive a 
specification file that is more easily readable, and last but not least, allows the user to compare the intended and 
actual implementation of an ABCI App. As such, there are three modalities:
- checking the ABCI App implementation
- generating a YAML or JSON specification file from the ABCI App using simplified human-readable syntax
- comparing the implementation of an ABCI App against a user generated YAML or JSON specification file


Example usage:
1. check \
`./check_abciapp_spec.py packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp`
2. generate \
`./check_abciapp_spec.py packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output_file.yaml`
3. compare \
`./check_abciapp_spec.py packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i output_file.yaml`

