<a id="autonomy.analyse.abci.app_spec"></a>

# autonomy.analyse.abci.app`_`spec

Generates the specification for a given ABCI app in YAML/JSON/Mermaid format.

JSON output is deprecated and will be removed in a future release; use YAML
or Mermaid instead.

<a id="autonomy.analyse.abci.app_spec.validate_fsm_spec"></a>

#### validate`_`fsm`_`spec

```python
def validate_fsm_spec(data: Dict) -> None
```

Validate FSM specificaiton file.

<a id="autonomy.analyse.abci.app_spec.DFASpecificationError"></a>

## DFASpecificationError Objects

```python
class DFASpecificationError(Exception)
```

Simple class to raise errors when parsing a DFA.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader"></a>

## FSMSpecificationLoader Objects

```python
class FSMSpecificationLoader()
```

FSM specification loader utilities.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.OutputFormats"></a>

## OutputFormats Objects

```python
class OutputFormats()
```

Output formats.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.from_yaml"></a>

#### from`_`yaml

```python
@staticmethod
def from_yaml(file: Path) -> Dict
```

Load from yaml.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.from_json"></a>

#### from`_`json

```python
@staticmethod
def from_json(file: Path) -> Dict
```

Load from json.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.load"></a>

#### load

```python
@classmethod
def load(cls, file: Path, spec_format: str = OutputFormats.YAML) -> Dict
```

Load FSM specification.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.dump_json"></a>

#### dump`_`json

```python
@staticmethod
def dump_json(dfa: "DFA", file: Path) -> None
```

Dump to a json file (deprecated).

JSON output is deprecated; prefer YAML or Mermaid. The
``DeprecationWarning`` is emitted by ``dump()`` so that
``stacklevel`` always points at the external caller.

**Arguments**:

- `dfa`: DFA object to serialize.
- `file`: Output file path.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.dump_yaml"></a>

#### dump`_`yaml

```python
@staticmethod
def dump_yaml(dfa: "DFA", file: Path) -> None
```

Dump to a yaml file.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.dump_mermaid"></a>

#### dump`_`mermaid

```python
@staticmethod
def dump_mermaid(dfa: "DFA",
                 file: Path,
                 abci_app_cls: Optional[_AbciAppLike] = None,
                 dev_skills: Optional[Set[str]] = None) -> None
```

Dumps this DFA spec. to a file in Mermaid format.

When ``abci_app_cls`` is supplied AND its rounds span more than one
sub-app, the diagram collapses every THIRD-PARTY sub-app into a
single node (one box per sub-app), and leaves dev sub-apps expanded
with their atomic rounds. ``dev_skills`` is the set of skill names
the local repo authored (typically derived from the ``dev`` section
of ``packages/packages.json``); any sub-app not in this set is
treated as third-party and collapsed.

Falls back to the flat per-round diagram when ``abci_app_cls`` is
``None``, when ``dev_skills`` is empty or ``None`` (i.e. no
packages.json info available), or when all rounds belong to a
single sub-app.

**Arguments**:

- `dfa`: DFA object to render.
- `file`: Output file path.
- `abci_app_cls`: Optional composed AbciApp class used to classify
rounds by sub-app for the composition-aware view.
- `dev_skills`: Optional set of dev skill names (from
``packages.json``); sub-apps not in this set are collapsed.

<a id="autonomy.analyse.abci.app_spec.FSMSpecificationLoader.dump"></a>

#### dump

```python
@classmethod
def dump(cls,
         dfa: "DFA",
         file: Path,
         spec_format: str = OutputFormats.YAML,
         abci_app_cls: Optional[_AbciAppLike] = None,
         dev_skills: Optional[Set[str]] = None) -> None
```

Dumps this DFA spec. to a file in YAML/JSON/Mermaid format.

``abci_app_cls`` and ``dev_skills`` are only used by the Mermaid
renderer to collapse third-party sub-apps into single nodes while
keeping dev sub-apps expanded (see ``dump_mermaid``). Other
formats ignore them.

**Arguments**:

- `dfa`: DFA object to serialize.
- `file`: Output file path.
- `spec_format`: One of ``OutputFormats.YAML``, ``JSON``, or
``MERMAID``.
- `abci_app_cls`: Optional composed AbciApp class (Mermaid only).
- `dev_skills`: Optional set of dev skill names (Mermaid only).

<a id="autonomy.analyse.abci.app_spec.DFA"></a>

## DFA Objects

```python
class DFA()
```

Simple specification of a deterministic finite automaton (DFA).

<a id="autonomy.analyse.abci.app_spec.DFA.__init__"></a>

#### `__`init`__`

```python
def __init__(label: str, states: Set[str], default_start_state: str,
             start_states: Set[str], final_states: Set[str],
             alphabet_in: Set[str], transition_func: Dict[Tuple[str, str],
                                                          str])
```

Initialize DFA object.

<a id="autonomy.analyse.abci.app_spec.DFA.validate_naming_conventions"></a>

#### validate`_`naming`_`conventions

```python
def validate_naming_conventions() -> None
```

Validate state names to see if they follow the naming conventions below

- A round name should end with `Round`
- ABCI app class name should end with `AbciApp`

<a id="autonomy.analyse.abci.app_spec.DFA.is_transition_func_total"></a>

#### is`_`transition`_`func`_`total

```python
def is_transition_func_total() -> bool
```

Outputs True if the transition function of the DFA is total.

A transition function is total when it explicitly defines all the transitions
for all the possible pairs (state, input_symbol). By convention, when a transition
(state, input_symbol) is not defined for a certain input_symbol, it will be
automatically regarded as a self-transition to the same state.

**Returns**:

True if the transition function is total. False otherwise.

<a id="autonomy.analyse.abci.app_spec.DFA.get_transitions"></a>

#### get`_`transitions

```python
def get_transitions(input_sequence: List[str]) -> List[str]
```

Runs the DFA given the input sequence of symbols, and outputs the list of state transitions.

<a id="autonomy.analyse.abci.app_spec.DFA.parse_transition_func"></a>

#### parse`_`transition`_`func

```python
def parse_transition_func() -> Dict[str, Dict[str, str]]
```

Parse the transition function from the spec to a nested dictionary.

<a id="autonomy.analyse.abci.app_spec.DFA.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: object) -> bool
```

Compares two DFAs

<a id="autonomy.analyse.abci.app_spec.DFA.generate"></a>

#### generate

```python
def generate() -> Dict[str, Any]
```

Retrieves an exportable representation for YAML/JSON dump of this DFA.

<a id="autonomy.analyse.abci.app_spec.DFA.load"></a>

#### load

```python
@classmethod
def load(
        cls,
        file: Path,
        spec_format: str = FSMSpecificationLoader.OutputFormats.YAML) -> "DFA"
```

Loads a DFA JSON specification from file.

<a id="autonomy.analyse.abci.app_spec.DFA.abci_to_dfa"></a>

#### abci`_`to`_`dfa

```python
@classmethod
def abci_to_dfa(cls, abci_app_cls: Any, label: str = "") -> "DFA"
```

Translates an AbciApp class into a DFA.

<a id="autonomy.analyse.abci.app_spec.check_unreferenced_events"></a>

#### check`_`unreferenced`_`events

```python
def check_unreferenced_events(abci_app_cls: Any) -> List[str]
```

Check for unreferenced events in the AbciApp.

For every round in the transition function, computes the set of events
the round can effectively emit and compares it to the events the FSM
expects.  An event is considered emitted if it is either:

1. The effective value of a ``*_event`` class attribute, resolved
   leaf-first through the MRO (so an override masks the parent value).
2. Referenced as ``Event.X`` in the source of the round or any of its
   non-builtin superclasses, with ``*_event = Event.X`` attribute
   definitions stripped out (those are covered by case 1, and a
   parent-class definition would otherwise be reported even after the
   subclass overrides the attribute).  When the AbciApp's Event enum
   can be identified, names absent from that enum are dropped to avoid
   cross-skill collisions (e.g. ``market_manager.Event.FETCH_ERROR``
   referenced from a parent class living in a different skill).
3. Declared via a ``# fsm-specs: returns(EVENT_NAME, ...)`` annotation
   on the round class -- the supported syntax for rounds that build
   events dynamically (e.g. ``Event(payload_value)``).

**Arguments**:

- `abci_app_cls`: AbciApp to check unreferenced events.

**Returns**:

List of error strings.

