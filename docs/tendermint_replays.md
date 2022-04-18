# Replay agents runs from Tendermint dumps

1. Run your preferred app in dev mode, for example run oracle in dev using `make run-oracle-dev` and in a separate terminal run `make run-hardhat`.

2. Wait until at least one reset (`reset_and_pause` round) has occurred, because the Tendermint server will only dump Tendermint data on resets. Once you have a data dump stop the app.

3. Run `python replay_scripts/fix_addrbooks.py`. If you're using a directory other than `deployments/build` to build agent and tendermint node configurations make sure to provide a build path to the script, `python replay_scripts/fix_addrbooks.py --build path/to/build/directory`.

4. Run `python replay_scripts/tendermint_runner.py` (Make sure to pass a build directory path in the same way as above, if relevant). This will spawn a tendermint network with the available dumps.

5. Now  you can run replays for particular agents using `python replay_scripts/agent_runner.py AGENT_ID`. `AGENT_ID` is a number between `0` and the number of available agents `-1`. E.g. `python replay_scripts/agent_runner.py 0` will run the replay for the first agent.
