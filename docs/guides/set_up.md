The purpose of this guide is to set up your system to work with the {{open_autonomy}} framework. All the remaining guides assume that you have followed these set up instructions.

## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.7` (recommended `>= 3.10`)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation/) `>=2021.x.xx`
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Set up the framework

1. **Create a workspace folder:**

    ```bash
    mkdir my_workspace
    cd my_workspace
    ```

    We recommend that you use a Pipenv virtual environment in your workspace folder. Remember to use the Python version you have installed. Here we are using 3.10 as reference:

    ```bash
    touch Pipfile && pipenv --python 3.10 && pipenv shell
    ```

2. **Install the {{open_autonomy}} framework:**

    ```bash
    pip install open-autonomy[all]
    ```

3. **Initialize the framework** to work with the remote [IPFS](https://ipfs.io) registry by default. This means that when the framework will be fetching a component, it will do so from the remote registry:

    ```bash
    autonomy init --remote --ipfs
    ```

    If you had previously initialized the framework, you need to use the flag `--reset` to change the configuration.

4. **Initialize the local registy:**

    ```bash
    autonomy packages init
    ```

    This will create an empty local registry in the `./packages` folder. If you plan to execute the tutorial guides, you need to [populate the local registry](#set-up-the-local-registry-for-the-guides) with a number of default components.

## The registries and runtime folders

As seen above, the framework works with two registries:

* The **remote registry**, where developers publish finalized software packages, similarly as Docker Hub images.
* The **local registry**, which stores packages being developed (`dev`), or fetched from the remote registry (`third_party`) to be used locally.

When running agents or service deployments locally, the framework fetches the required components in the corresponding folder, or it might create auxiliary files and folders. For this reason, we recommend that **runtime folders** for agents and services be located outside the local registry to avoid publishing unintended files on the remote registry.

This is roughly how your workspace should look like:

<figure markdown>
![](../images/workspace.svg)
</figure>

!!! tip

    You can override the default registry in use (set up with `autonomy init`) for a particular command through the flags `--registry-path` and `--local`. For example, if the framework was initialized with the remote registry, the following command will fetch a runtime folder for the `hello_world` agent:

    ```bash
    autonomy fetch valory/hello_world:0.1.0:bafybeie26bvs657tcmaoxdkulzxpkr5uye26o4xp3scyllnuv5yk7izbbq
    ```

    If you want to fetch the copy stored in your local registry, then use the following command:
    ```bash
    autonomy --registry-path=./packages fetch valory/hello_world:0.1.0 --local
    ```

## The Dev template

For convenience, we provide a **Dev template** repository that you can fork and clone for your Open Autonomy projects, and use it as your workspace folder:

<figure markdown>
[https://github.com/valory-xyz/dev-template](https://github.com/valory-xyz/dev-template)
</figure>

The **Dev template** comes with:

* a preconfigured Pipenv environment with required dependencies,
* an empty local registry,
* a number of preconfigured linters via [Tox](https://tox.wiki/en/latest/).

## Set up the local registry for the guides

If you plan to follow the guides in the next sections, you need to populate the local registry with a number of default [packages shipped with the framework](../package_list.md). To do so, within the workspace folder, execute:

```bash
cat > ./packages/packages.json << EOF
{
    "dev": {
    },
    "third_party": {
        {{ get_packages_entry("agent/valory/hello_world/0.1.0") }},
        {{ get_packages_entry("connection/valory/abci/0.1.0") }},
        {{ get_packages_entry("connection/valory/http_client/0.23.0") }},
        {{ get_packages_entry("connection/valory/ipfs/0.1.0") }},
        {{ get_packages_entry("connection/valory/ledger/0.19.0") }},
        {{ get_packages_entry("connection/valory/p2p_libp2p_client/0.1.0") }},
        {{ get_packages_entry("contract/valory/service_registry/0.1.0") }},
        {{ get_packages_entry("protocol/open_aea/signing/1.0.0") }},
        {{ get_packages_entry("protocol/valory/abci/0.1.0") }},
        {{ get_packages_entry("protocol/valory/acn/1.1.0") }},
        {{ get_packages_entry("protocol/valory/contract_api/1.0.0") }},
        {{ get_packages_entry("protocol/valory/http/1.0.0") }},
        {{ get_packages_entry("protocol/valory/ipfs/0.1.0") }},
        {{ get_packages_entry("protocol/valory/ledger_api/1.0.0") }},
        {{ get_packages_entry("protocol/valory/tendermint/0.1.0") }},
        {{ get_packages_entry("skill/valory/abstract_abci/0.1.0") }},
        {{ get_packages_entry("skill/valory/abstract_round_abci/0.1.0") }},
        {{ get_packages_entry("skill/valory/hello_world_abci/0.1.0") }}
    }
}
EOF
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.
