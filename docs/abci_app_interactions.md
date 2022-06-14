# Interactions between Components in an {{fsm_app}}

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
AEA event loop.

<div class="mermaid">
    sequenceDiagram
        participant EventLoop
        participant AbsRoundBehaviour
        participant Behaviour1
        participant Behaviour2
        participant SharedState
        note over AbsRoundBehaviour,Behaviour2: Let the FSM App start with Behaviour1<br/>it will schedule Behaviour2 on event e.
        loop while round does not change
          EventLoop->>AbsRoundBehaviour: act()
          AbsRoundBehaviour->>Behaviour1: act()
          activate Behaviour1
          note over Behaviour1: During the execution, <br/> the current round may<br/>(or may not) change.
          Behaviour1->>AbsRoundBehaviour: return
          deactivate Behaviour1
          note over EventLoop: The loop now executes other routines.
        end
        note over AbsRoundBehaviour: Read current AbciApp round and pick matching state<br/>in this example, Behaviour2.
        EventLoop->>AbsRoundBehaviour: act()
        note over AbsRoundBehaviour: Now State2 act() is called.
        AbsRoundBehaviour->>Behaviour2: act()
        activate Behaviour2
        Behaviour2->>AbsRoundBehaviour: return
        deactivate Behaviour2
</div>



The following diagram describes the addition of transactions to the transaction
pool:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIRoundHandler
        participant SharedState
        participant Round
        activate Round
        note over ConsensusEngine,ABCIRoundHandler: client submits transaction tx
        ConsensusEngine->>ABCIRoundHandler: [Request] CheckTx(tx)
        ABCIRoundHandler->>SharedState: check_tx(tx)
        SharedState->>Round: check_tx(tx)
        Round->>SharedState: OK
        SharedState->>ABCIRoundHandler: OK
        ABCIRoundHandler->>ConsensusEngine: [Response] CheckTx(tx)
        note over ConsensusEngine,ABCIRoundHandler: tx is added to tx pool
</div>

The following diagram describes the delivery of transactions in a block:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIRoundHandler
        participant SharedState
        participant Round1
        participant Round2
        activate Round1
        note over Round1,Round2: Round1 is the active round,<br/>Round2 is the next round.
        note over ConsensusEngine,ABCIRoundHandler: Validated block ready to<br/>be submitted to the FSM App.
        ConsensusEngine->>ABCIRoundHandler: [Request] BeginBlock()
        ABCIRoundHandler->>SharedState: begin_block()
        SharedState->>ABCIRoundHandler: [Response] BeginBlock(OK)
        ABCIRoundHandler->>ConsensusEngine: OK
        loop for tx_i in block
            ConsensusEngine->>ABCIRoundHandler: [Request] DeliverTx(tx_i)
            ABCIRoundHandler->>SharedState: deliver_tx(tx_i)
            SharedState->>Round1: deliver_tx(tx_i)
            Round1->>SharedState: OK
            SharedState->>ABCIRoundHandler: OK
            ABCIRoundHandler->>ConsensusEngine: [Response] DeliverTx(OK)
        end
        ConsensusEngine->>ABCIRoundHandler: [Request] EndBlock()
        ABCIRoundHandler->>SharedState: end_block()
        alt if condition is true
            note over SharedState,Round1: Replace Round1 with Round2.
            deactivate Round1
            SharedState->>Round2: schedule
            activate Round2
        end
        SharedState->>ABCIRoundHandler: OK
        ABCIRoundHandler->>ConsensusEngine: [Response] EndBlock(OK)
        deactivate Round2
</div>
