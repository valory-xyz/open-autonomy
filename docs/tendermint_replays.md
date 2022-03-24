# Replay agents runs from tendermint dumps

1. Run your preferred app in dev mode, for example run oracle in dev using `make run-oracle-dev` and in a separate terminal run `make run-hardhat`.
2. Wait until at least one reset because tendermint server will only dump tendermint data on resets. Once you have a data dump stop the app.
3. Run `replay_scripts/fix_addrbooks.py`. If you're using directory other then `deployments/build` to build agent and tendermint node configs make sure to provide build path to script, `python replay_scripts/fix_addrbooks.py --build path/to/build/directory`
4. Run `replay_scripts/tendermint_runner.py` (Make sure to pass build directory path in same way as above). This will spawn a tendermint network with available dumps.
5. Now  you can run replays for perticular agents using `python replay_scripts/agent_runner.py AGENT_ID`. `AGENT_ID` is number between 0 and number of available agents. Eg. `python replay_scripts/agent_runner.py 0`.