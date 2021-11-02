### Consensus Time Benchmarks.

> To run benchmarks

```bash
./benchmark.sh 8
```

> To aggregate the benchmark results

```bash
python3 aggregate_results.py
```

> To experiment with different block time change timeout values in update_tendermint_timeouts.py.

```python
timeout_config_data = {
    # How long we wait for a proposal block before prevoting nil
    "timeout_propose": 3000,  # default: 3000

    # How much timeout_propose increases with each round
    "timeout_propose_delta": 500,  # default: 500
    
    # How long we wait after receiving +2/3 prevotes for “anything” (ie. not a single block or nil)
    "timeout_prevote": 1000,  # default: 1000

    # How much the timeout_prevote increases with each round
    "timeout_prevote_delta": 500,  # default: 500

    # How long we wait after receiving +2/3 precommits for “anything” (ie. not a single block or nil)
    "timeout_precommit": 1000,  # default: 1000

    # How much the timeout_precommit increases with each round
    "timeout_precommit_delta": 500,  # default: 500

    # How long we wait after committing a block, before starting on the new
    # height (this gives us a chance to receive some more precommits, even
    # though we already have +2/3).
    "timeout_commit": 1000,  # default: 1000
}
```

> To clean the benchmarking environment.

```bash
make clean-benchmark-env
```