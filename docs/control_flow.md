# Application Control Flow

!!! info
    This section is under review and will be updated soon.

Within a deployment, each individual agent in the service manages:
- a Tendermint Node
- an ABCI application

Each of the agents - containing the ABCI app - and the Tendermint node, are implemented as a Docker image which are deployed in a 1-2-1 relationship.

The Tendermint process is managed by a separate process, via a Flask server. The image containing the Flask server and Tendermint node are built on top of the ```valory/tendermint``` image.

## Tendermint Image control flow.

<div class="mermaid">
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
</div>


<div class="mermaid">
flowchart LR
    subgraph AEA Container
        start.sh --> A[Pull Aea]
        A --> b[Run AEA]
        subgraph AEA Process
            b[Run AEA]
        end
        b-->LOG[Log File]
    end
</div>


# Gentle Restart flow
<div class="mermaid">
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
</div>

This can be viewed in the logs as;
```bash

tail -f /logs/node_0.txt

Monitoring thread terminated
Tendermint process stopped
Tendermint process started
Monitoring thread started

```



# Hard Restart flow
<div class="mermaid">
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
</div>

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
When we have an issue with the AEA losing connection to the Tendermint process, caused by failure of the AEA, the sudden closure of the TCP connection will trigger a restart of the Tendermint process.

This failure of connection could be caused by a re-scheduling of the pod to another host within the cluster, or by another unexpected restart of the AEA container.

This can be simulated by kill a running aea-process while running a docker-compose deployment.

This will interrupt the TCP connection between the AEA and the Tendermint process, managed by the Flask process. The typical behaviour for Tendermint upon such an event is to stop the module responsible for handling *all* http traffic. We watch for this event, and then restart the Tendermint process upon detecting it.


```bash
# kill the aea
docker-compose kill abci0 && docker-compose up -d abci0
```

```bash
tail -f deployments/persistent_data/logs/node_0.txt

Tendermint process stopped
Tendermint process started
Restarted the HTTP RPC server, as a connection was dropped with message:
		 E[2022-05-11|13:15:11.368] Stopping abci.socketClient for error: read message: EOF module=abci-client connection=consensus
```


<div class="mermaid">
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
</div>

# Tendermint Network interruption Flow
When we have an issue with the Tendermint process connecting to the AEA, the sudden closure of the TCP connection will trigger a restart of the tendermint process.

The effect of this on the AEA, can be demonstrated as so;
```bash
# kill the node
docker-compose kill node0 && docker-compose up -d node0
```
The logs for the associated AEA show;

```bash
[2022-05-11 13:35:31,336] [INFO] [agent] Entered in the 'validate_oracle' round for period 0
[2022-05-11 13:35:31,338] [INFO] [agent] Entered in the 'validate_oracle' behaviour state
[2022-05-11 13:35:31,776] [ERROR] [agent] an error occurred while reading a message: DecodeVarintError: could not decode varint. The message will be ignored.
[2022-05-11 13:35:31,777] [INFO] [agent] connection at EOF, stop receiving loop.
[2022-05-11 13:35:31,777] [ERROR] [agent] an error occurred while reading a message: DecodeVarintError: could not decode varint. The message will be ignored.
[2022-05-11 13:35:31,777] [INFO] [agent] connection at EOF, stop receiving loop.
[2022-05-11 13:35:31,777] [ERROR] [agent] an error occurred while reading a message: DecodeVarintError: could not decode varint. The message will be ignored.
[2022-05-11 13:35:31,777] [INFO] [agent] connection at EOF, stop receiving loop.
[2022-05-11 13:35:31,777] [ERROR] [agent] an error occurred while reading a message: DecodeVarintError: could not decode varint. The message will be ignored.
[2022-05-11 13:35:31,777] [INFO] [agent] connection at EOF, stop receiving loop.
[2022-05-11 13:35:35,083] [INFO] [agent] arrived block with timestamp: 2022-05-11 13:35:31.193869
[2022-05-11 13:35:35,083] [INFO] [agent] current AbciApp time: 2022-05-11 13:35:29.879421
[2022-05-11 13:35:35,127] [INFO] [agent] 'validate_oracle' round is done with event: Event.DONE
[2022-05-11 13:35:35,128] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-05-11 13:35:38.193869
```
Notice how the AEA continues as soon as it is able to re-establish a connection.


<div class="mermaid">
sequenceDiagram
   AEA-->+AEA: starts_up
   FlaskServer-->+FlaskServer: starts_com_server
   FlaskServer-->+MonitoringThread: starts_monitoring_thread
   FlaskServer-->+TendermintProcess: starts_tendermint_process

   AEA->>+TendermintProcess: tcp port 26557
   TendermintProcess->>+AEA: loses connection
   TendermintProcess->>+TendermintProcess: HTTPServer crashes
   MonitoringThread->>+TendermintProcess: restart Tendermint process
   AEA->>+TendermintProcess: reconnects on tcp port
   TendermintProcess->>+AEA: tcp port 26558
</div>
