In this section we present sequence diagrams in order to help understand the transmitted messages and method calls between the software components that are part of an {{fsm_app}}.



## The `ABCIApp` - `AbstractRoundBehaviour` interaction

The interaction between `AbstractRoundBehaviour` and the `ABCIApp` occurs via
the consensus engine, the setup of which proceeds on the `Period`.
and the shared state among the skills. A typical workflow
looks as follows:

1. At setup time, the consensus engine node creates connections with the
   associated AEA and sync together. In the AEA process, the ABCIApp starts from
   the first round, waiting for transactions to update its state. The
   `AbstractRoundBehaviour` schedules the initial state behaviour for execution
   of the `act()` method.

2. The current state behaviour sends transactions to update the state of the
   `ABCIApp`, and once its job is done waits until it transitions to the next
   round, by checking read-only attributes of the `ABCIApp` accessible through
   the AEAs' skill context. Concrete implementations of `AbstractRoundBehaviour`
   cannot update the state the of ABCIApp directly, only through an agreed
   upon update with other agents via the consensus engine node.

3. Once the transaction gets added to a block accepted by the consensus engine,
   the consensus engine node delivers the block and transactions contained in
   it to the `ABCIApp` using the AEAs `ABCIConnection` and `ABCIHandler`. The
   `ABCIApp` processes the transaction and enacts the encoded state transition
   logic.

4. The transition to the next round is detected and all scheduled behaviour and
   other tasks get cancelled before transitioning to the next round.

5. Cycles of such rounds may, either entirely or in part, be repeated until a
   final state is reached, implemented as a


## AbstractRoundBehaviour:

Concrete implementations of `AbstractRoundBehaviour` can be seen as a _client_
of the `ABCIApp` (in that sense it encapsulates the "user" of a normal blockchain).


### AbstractRoundBehaviour diagrams

The following diagram shows how the FSM behaviour operates in concert with the
AEA event loop. (Not all components are included in the diagram.)

<div class="mermaid">
    sequenceDiagram
        participant EventLoop
        participant AbsRoundBehaviour
        participant Behaviour1
        participant Behaviour2
        participant Outbox
        note over AbsRoundBehaviour,Behaviour2: Let the FSM App start with Behaviour1<br/>it will schedule Behaviour2 on event e.
        loop while round does not change
          EventLoop->>AbsRoundBehaviour: act()
          alt if Behaviour1 not done
            note over AbsRoundBehaviour: Behaviour1 act() is called.
            AbsRoundBehaviour->>Behaviour1: act()
            activate Behaviour1
            note over Behaviour1: During the execution, <br/> the current round may<br/>(or may not) change.
            Behaviour1->>Outbox: put_message("GET (...) /tx_sync=0x(...)")
            Behaviour1->>Outbox: [Wait until tx delivered] put_message("GET (...) /tx?hash=0x(...)")
            note over Outbox: Multiplexer will route the transactions<br/>to the corresponding connection.
            Behaviour1->>AbsRoundBehaviour: return
            deactivate Behaviour1
          else
            AbsRoundBehaviour->>Behaviour1: clean_up()
          end
          note over EventLoop: Other routines.
        end
        note over AbsRoundBehaviour: Read current AbciApp round and pick matching Behaviour<br/>in this example, Behaviour2.
        loop while round does not change
        EventLoop->>AbsRoundBehaviour: act()

        note over AbsRoundBehaviour: Now Behaviour2 act() is called.
        AbsRoundBehaviour->>Behaviour2: act()
        activate Behaviour2
        Behaviour2->>AbsRoundBehaviour: return
        deactivate Behaviour2
        note over EventLoop: Other routines.        
        end
</div>



The following diagram describes the addition of transactions to the transaction
pool. (Not all components are included in the diagram.)

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIServerConnection as ABCIServerConnection<br/>TendermintDecoder
        participant ABCIRoundHandler
        note over ConsensusEngine,ABCIServerConnection: client submits transaction tx
        ConsensusEngine->>ABCIServerConnection: [Request] CheckTx(tx)
        ABCIServerConnection->>ABCIRoundHandler: check_tx(tx)
        ABCIRoundHandler->>RoundSequence: check_is_finished()
        RoundSequence->>ABCIRoundHandler: false
        ABCIRoundHandler->>ABCIServerConnection: OK
        ABCIServerConnection->>ConsensusEngine: [Response] CheckTx(tx)
        note over ConsensusEngine,ABCIServerConnection: tx is added to tx pool
        ConsensusEngine->>ABCIServerConnection: [Request] DeliverTx(tx)
        ABCIServerConnection->>ABCIRoundHandler: deliver_tx(tx)
        ABCIRoundHandler->>RoundSequence: check_is_finished()
        RoundSequence->>ABCIRoundHandler: false
        ABCIServerConnection->>RoundSequence: deliver_tx(tx)
        RoundSequence->>ABCIApp: check_transaction(tx)             
        ABCIApp->>Round: check_transaction(tx)                
        Round->>ABCIApp: OK
        ABCIApp->>RoundSequence: OK
        RoundSequence->>ABCIRoundHandler: OK        
        ABCIRoundHandler->>ABCIServerConnection: OK
        ABCIServerConnection->>ConsensusEngine: [Response] CheckTx(tx)        
</div>

The following diagram describes the delivery of transactions in a block:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIServerConnection as ABCIServerConnection<br/>TendermintDecoder
        participant ABCIRoundHandler
        participant RoundSequence
        participant ABCIApp
        participant Round1
        participant Round2
        activate Round1
        note over Round1,Round2: Round1 is the active round,<br/>Round2 is the next round.
        note over ConsensusEngine,ABCIRoundHandler: Validated block ready to<br/>be submitted to the FSM App.
        ConsensusEngine->>ABCIServerConnection: [Request] BeginBlock()
        ABCIServerConnection->>ABCIRoundHandler: begin_block()        
        ABCIRoundHandler->>RoundSequence: begin_block()
        ABCIRoundHandler->>ABCIServerConnection: OK
        ABCIServerConnection->>ConsensusEngine: [Response] BeginBlock(OK)
        loop for tx_i in block
          ConsensusEngine->>ABCIServerConnection: [Request] DeliverTx(tx)
          ABCIServerConnection->>ABCIRoundHandler: deliver_tx(tx)
          ABCIRoundHandler->>RoundSequence: check_is_finished()
          RoundSequence->>ABCIRoundHandler: false
          ABCIServerConnection->>RoundSequence: deliver_tx(tx)
          RoundSequence->>ABCIApp: check_transaction(tx)             
          ABCIApp->>Round1: check_transaction(tx)                
          Round1->>ABCIApp: OK
          ABCIApp->>RoundSequence: OK
          RoundSequence->>ABCIRoundHandler: OK        
          ABCIRoundHandler->>ABCIServerConnection: OK
          ABCIServerConnection->>ConsensusEngine: [Response] CheckTx(tx)   
        end
        ConsensusEngine->>ABCIServerConnection: [Request] EndBlock()
        ABCIServerConnection->>ABCIRoundHandler: end_block()
        ABCIRoundHandler->>RoundSequence: end_block()
        alt if condition is true
            note over Round1, Round2: Replace Round1 with Round2.
            deactivate Round1
            RoundSequence->>Round2: schedule (*)
            activate Round2
        end
        RoundSequence->>ABCIRoundHandler: OK
        ABCIRoundHandler->>ABCIServerConnection: OK
        ABCIServerConnection->>ConsensusEngine: [Response] EndBlock(OK)
        deactivate Round2
</div>
