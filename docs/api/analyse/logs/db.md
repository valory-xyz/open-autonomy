<a id="autonomy.analyse.logs.db"></a>

# autonomy.analyse.logs.db

Database schemas and helpers

<a id="autonomy.analyse.logs.db.AgentLogsDB"></a>

## AgentLogsDB Objects

```python
class AgentLogsDB()
```

Logs DB

<a id="autonomy.analyse.logs.db.AgentLogsDB.__init__"></a>

#### `__`init`__`

```python
def __init__(agent: str, file: Path) -> None
```

Initialize object.

<a id="autonomy.analyse.logs.db.AgentLogsDB.select"></a>

#### select

```python
def select(start_time: Optional[datetime] = None,
           end_time: Optional[datetime] = None,
           log_level: Optional[str] = None,
           period: Optional[int] = None,
           round_name: Optional[str] = None,
           behaviour_name: Optional[str] = None) -> List[LogRow]
```

Build select query.

<a id="autonomy.analyse.logs.db.AgentLogsDB.execution_path"></a>

#### execution`_`path

```python
def execution_path() -> List[Tuple[int, str, str]]
```

Extraction FSM execution path

<a id="autonomy.analyse.logs.db.AgentLogsDB.cursor"></a>

#### cursor

```python
@property
def cursor() -> sqlite3.Cursor
```

Creates and returns a database cursor.

<a id="autonomy.analyse.logs.db.AgentLogsDB.exists"></a>

#### exists

```python
def exists() -> bool
```

Check if table already exists.

<a id="autonomy.analyse.logs.db.AgentLogsDB.delete"></a>

#### delete

```python
def delete() -> "AgentLogsDB"
```

Delete table

<a id="autonomy.analyse.logs.db.AgentLogsDB.create"></a>

#### create

```python
def create(reset: bool = False) -> "AgentLogsDB"
```

Create agent table

<a id="autonomy.analyse.logs.db.AgentLogsDB.insert_many"></a>

#### insert`_`many

```python
def insert_many(logs: Iterator[LogRow]) -> "AgentLogsDB"
```

Insert a record

