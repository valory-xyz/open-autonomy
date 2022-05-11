# Application Control Flow

Within a deployment, each individual tendermint node consists of a:
- Tendermint Node
- ABCI application

Each of these is implemented as a docker image which is deployed in a 1-2-1 relationship.

The tendermint image is implemented as a flask server built on top of the ```valory/tendermint``` image.

## Tendermint Image control flow. 

```mermaid
flowchart TD
    subgraph Tendermint  Container
        A[Flask EntryPoint] --> Flask
        STDOUT --> Monitoring
        Monitoring --> LOG
        Flask --> LOG
        Flask --> Monitoring
        Flask --> StartA
        
        subgraph FP[Flask Process]
            Flask((Flask Server))
            subgraph Tendermint Process
                Tendermint((Tendermint Process))
                StartA[Tendermint Process] --> Tendermint
                Tendermint --> STDOUT[STDOUT]
            end
            subgraph Monitoring Thread
                Monitoring((Monitoring Thread))
            end
        end
    end
```


```mermaid
flowchart LR
    subgraph AEA Container
        start.sh --> A[Pull Aea]
        A --> b[Run AEA]
        subgraph AEA Process
            b[Run AEA]
        end
        b-->LOG[Log File]
    end
```

# Gentle Restart flow
```mermaid
sequenceDiagram
   AEA-->+AEA: starts_up
   FlaskServer-->+FlaskServer: starts_com_server
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
   FlaskServer-->+TendermintProcess: starts_tendermint_process
   
   AEA->>+TendermintProcess: port 26557
   TendermintProcess->>+AEA: port 26558 
   
   AEA->>+FlaskServer: gentle_reset
   FlaskServer-->+FlaskServer: stops_monitoring_thread
   FlaskServer-->+FlaskServer: stops_tendermint_process
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
   FlaskServer-->+TendermintProcess: starts_tendermint_process
```
This can viewed in the logs as;
```bash

tail -f /logs/node_0.txt

Monitoring thread terminated
Tendermint process stopped
Tendermint process started
Monitoring thread started

```



# Hard Restart flow
```mermaid
sequenceDiagram
   AEA-->+AEA: starts_up
   FlaskServer-->+FlaskServer: starts_com_server
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
   FlaskServer-->+TendermintProcess: starts_tendermint_process
   
   AEA->>+TendermintProcess: port 26557
   TendermintProcess->>+AEA: port 26558 
   
   AEA->>+FlaskServer: hard_reset
   FlaskServer-->+FlaskServer: stops_monitoring_thread
   FlaskServer-->+FlaskServer: stops_tendermint_process
   FlaskServer-->+TendermintProcess: prune_blocks
   FlaskServer-->+TendermintProcess: starts_tendermint_process
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
```

```bash
E[2022-05-11|13:45:41.355] abci.socketClient failed to connect to tcp://localhost:26658.  Retrying after 3s... module=abci-client connection=query err="dial tcp 127.0.0.1:26658: connect: connection refused"
Monitoring thread terminated
Tendermint process stopped
Tendermint process started
Monitoring thread started
I[2022-05-11|13:45:41.450] Starting multiAppConn service                module=proxy impl=multiAppConn
```

Simultaneously, the flask server will display;

```
I[2022-05-11|13:45:41.389] Removed existing address book                module=main file=/tendermint/node1/config/addrbook.json
I[2022-05-11|13:45:41.389] Removed all blockchain history               module=main dir=/tendermint/node1/data
I[2022-05-11|13:45:41.395] Reset private validator file to genesis state module=main keyFile=/tendermint/node1/config/priv_validator_key.json stateFile=/tendermint/node1/data/priv_validator_state.json
```



# AEA Network interruption Flow

```mermaid
sequenceDiagram
   AEA-->+AEA: starts_up
   FlaskServer-->+FlaskServer: starts_com_server
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
   FlaskServer-->+TendermintProcess: starts_tendermint_process
   
   AEA->>+TendermintProcess: tcp port 26557
   TendermintProcess->>+AEA: tcp port 26558
   AEA->>+TendermintProcess: loses connection/breaktcp connection
   TendermintProcess->>+TendermintProcess: HTTPServer crashes
   MonitoringThread->>+TendermintProcess: restart Tendermint process

   AEA->>+TendermintProcess: reconnects on tcp port
   TendermintProcess->>+AEA: tcp port 26558
```

# Tendermint Network interruption Flow

```mermaid
sequenceDiagram
   AEA-->+AEA: starts_up
   FlaskServer-->+FlaskServer: starts_com_server
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
   FlaskServer-->+TendermintProcess: starts_tendermint_process
   
   AEA->>+TendermintProcess: tcp port 26557
   TendermintProcess->>+AEA: losses connection
   TendermintProcess->>+TendermintProcess: HTTPServer crashes
   MonitoringThread->>+TendermintProcess: restart Tendermint process
   AEA->>+TendermintProcess: reconnects on tcp port
   TendermintProcess->>+AEA: tcp port 26558
```
