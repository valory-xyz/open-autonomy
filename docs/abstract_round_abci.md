The `abstract_round_abci` skill implements the abstract classes for implementation of a fully replicated FSM application.

The following concepts are important:

- period: A period is a sequence of rounds. The relevant class `Period` (in `base_models.py`) is the core object. It is instantiated in the `SharedState` model which is available on the skill context.


- The `AbstractRoundBehaviour` (in `behaviours.py`) is the extension of the FSM class. It needs to be extended on the application level and provided with a list of all states.
