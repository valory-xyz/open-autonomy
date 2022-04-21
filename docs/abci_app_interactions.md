# Interactions between Components in an {{abci_app}}

In this section we present sequence diagrams in order to help understand the transmitted messages and method calls between the software components that are part of an {{abci_app}}.



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
        participant State1
        participant State2
        participant Period
        note over AbsRoundBehaviour,State2: Let the FSMBehaviour start with State1<br/>it will schedule State2 on event e
        loop while round does not change
          EventLoop->>AbsRoundBehaviour: act()
          AbsRoundBehaviour->>State1: act()
          activate State1
          note over State1: during the execution, <br/> the current round may<br/>(or may not) change
          State1->>AbsRoundBehaviour: return
          deactivate State1
          note over EventLoop: the loop now executes other routines
        end
        note over AbsRoundBehaviour: read current AbciApp round and pick matching state<br/>in this example, State2
        EventLoop->>AbsRoundBehaviour: act()
        note over AbsRoundBehaviour: now State2.act is called
        AbsRoundBehaviour->>State2: act()
        activate State2
        State2->>AbsRoundBehaviour: return
        deactivate State2
</div>



The following diagram describes the addition of transactions to the transaction
pool:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIHandler
        participant Period
        participant Round
        activate Round
        note over ConsensusEngine,ABCIHandler: client submits transaction tx
        ConsensusEngine->>ABCIHandler: RequestCheckTx(tx)
        ABCIHandler->>Period: check_tx(tx)
        Period->>Round: check_tx(tx)
        Round->>Period: OK
        Period->>ABCIHandler: OK
        ABCIHandler->>ConsensusEngine: ResponseCheckTx(tx)
        note over ConsensusEngine,ABCIHandler: tx is added to tx pool
</div>

The following diagram describes the delivery of transactions in a block:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIHandler
        participant Period
        participant Round1
        participant Round2
        activate Round1
        note over Round1,Round2: Round1 is the active round,<br/>Round2 is the next round
        note over ConsensusEngine,ABCIHandler: validated block ready to<br/>be submitted to the ABCI app
        ConsensusEngine->>ABCIHandler: RequestBeginBlock()
        ABCIHandler->>Period: begin_block()
        Period->>ABCIHandler: ResponseBeginBlock(OK)
        ABCIHandler->>ConsensusEngine: OK
        loop for tx_i in block
            ConsensusEngine->>ABCIHandler: RequestDeliverTx(tx_i)
            ABCIHandler->>Period: deliver_tx(tx_i)
            Period->>Round1: deliver_tx(tx_i)
            Round1->>Period: OK
            Period->>ABCIHandler: OK
            ABCIHandler->>ConsensusEngine: ResponseDeliverTx(OK)
        end
        ConsensusEngine->>ABCIHandler: RequestEndBlock()
        ABCIHandler->>Period: end_block()
        alt if condition is true
            note over Period,Round1: replace Round1 with Round2
            deactivate Round1
            Period->>Round2: schedule
            activate Round2
        end
        Period->>ABCIHandler: OK
        ABCIHandler->>ConsensusEngine: ResponseEndBlock(OK)
        deactivate Round2
</div>
