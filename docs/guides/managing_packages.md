
## Creating your agents and services

The first thing a developer needs to do before they start writing code is setting up the project. Instead of starting from scratch, we recommend to clone our [developer template](https://github.com/valory-xyz/dev-template). Once setup, it will generate a virtual environment with {{open_autonomy}} installed, an empty local registry, some useful tools for checking packages and dummy tests. After this, in the same fashion Git asks to initialize its configuration using `git config`, {{open_autonomy}} asks the user to set the user name, whether we are using a local or remote registry as well as the type of registry (IPFS by default). For example, initialize your registry running the following command:

```bash
autonomy init --reset --author john_doe --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"
```

Now we are in the position of creating our first agent:

```bash
autonomy create my_agent
```

This agent will have some dependencies: some packages might be already available in the remote registry and some will need to be developed. Let's say, for example, that it will need the ability to use the signing protocol protocol. Since that package is already available on the Autonolas IPFS registry, we'll use the `add command`:

```bash
cd my_agent/
# Remote flag is not needed here as we initialized the default registry to remote
autonomy add protocol open_aea/signing:1.0.0:bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44
```


Now we might want to develop our own package, for example a skill. We could do it writing all the skill structure from scratch, but fortunately the CLI also provides a scaffolding option that will create a lot of boilerplate for us using its specification. For this example, we will use the specification from the [hello world skill](https://raw.githubusercontent.com/valory-xyz/open-autonomy/main/packages/valory/skills/hello_world_abci/fsm_specification.yaml). Download it to the agent directory and run:

```bash
autonomy scaffold fsm my_skill --spec fsm_specification.yaml
```

This will add your skill's boilerplate code to `my_agent/skills/my_skill` and some dependencies to the vendor directory. You can learn more on scaffolding by reading the [create a service from scratch](./create_service_from_scratch.md) guide.

Now that we have all we need, publish the new agent and all its dependencies to the local registry:

```bash
autonomy publish --local --push-missing
```

The agent and its dependencies live now in the local registry, so we can delete the temporary agent:

```bash
cd ..
autonomy delete my_agent
```

We will focus now on developing inside the local registry. First of all, it is useful to add other vendor paths to the `.gitignore` (for example `packages/valory` and `packages/open-aea`) so only your packages are tracked. Secondly, even if the skill is now in the local registry, there is another task we need to perform: update the `packages/packages.json` file. This file contains a list of all packages in the registry, as well as their hashes. It's useful to detect when packages change, are added or removed. If you open that file you will see it is empty. To reflect our latest changes, run:

```bash
autonomy packages lock
```

While developing, each change will make this hashes out of date. You can run the following to check whether you need to update `autonomy packages lock` again:

```bash
autonomy packages lock --check
```

Each time you need a new package, add its identifier to `packages.json`, run `autonomy packages sync --update-packages` to download it and then add it to the agent's configuration file.

## The remote registry

We have been mostly working with the local registry, but for other developers to be able to fetch your packages you will need to push them to the remote registry: `push`, `publish`, `add` and `fetch` commands work with the `--remote` flag. When you specify it instead of the `--local` one, operations will be performed against a remote server. You can also push a package directly from the local registry to the remote one:

```bash
# Remove all cache files before running
autonomy push skill packages/john_doe/skills/my_skill/ --remote
```

Or maybe you prefer to push all your packages in one step:

```bash
# Remove all cache files before running
autonomy push-all --remote
```

Remember how we updated the package hashes when we edited packages in the local registry? It is good practice to keep your `packages.json` updated so it matches the state of your packages. This also applies to the remote registry. Sometimes you want to be sure that a package you have fetched has not been modified. When a package is out of sync, you have two options:

- Update your local hashes to match the remote package:
```bash
autonomy packages sync --update-hashes
```

- Re-download the packages whose hashes do not match:
```bash
autonomy packages sync --update-packages
```
