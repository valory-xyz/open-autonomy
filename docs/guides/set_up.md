The purpose of this guide is to set up your system to work with the {{open_autonomy}} framework. All the remaining guides assume that you have followed these set up instructions.

## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.8` (recommended `>= 3.10`)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html) `>=2021.x.xx`
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Additionally, if you wish to deploy your service in a Kubernetes cluster:

- [Kubernetes CLI](https://kubernetes.io/docs/tasks/tools/)
- [minikube](https://minikube.sigs.k8s.io/docs/)


!!! note
    On raspberry-pi currently `Raspberry Pi OS (Legacy, 64-bit, Debian Bullseye)` is tested and supported, The base requirements are same as [above](#requirements).

!!! tip
	Although we will use these tools for demonstration purposes only, you might as well consider other local Kubernetes cluster options like [kind](https://kind.sigs.k8s.io/docs/user/quick-start/), or even additional tools like [Skaffold](https://skaffold.dev/) or [Helm](https://helm.sh/) to help you with your cluster deployments.

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

2. **Install the {{open_autonomy}} framework and the [Open AEA Ethereum Ledger Plugin](https://pypi.org/project/open-aea-ledger-ethereum):**

    ```bash
    pip install open-autonomy[all]
    pip install open-aea-ledger-ethereum
    ```

3. **Initialize the framework** to work with the remote [IPFS](https://ipfs.io) registry by default. This means that when the framework will be fetching a component, it will do so from the remote registry:

    ```bash
    autonomy init --remote --ipfs
    ```

    If you had previously initialized the framework, you need to use the flag `--reset` to change the configuration.

4. **Initialize the local registry:**

    ```bash
    autonomy packages init
    ```

    This will create an empty local registry in the `./packages` folder. If you plan to execute the tutorial guides, you need to [populate the local registry](#populate-the-local-registry-for-the-guides) with a number of default components.

## The registries and runtime folders

As seen above, the framework works with two registries:

* The **remote registry**, where developers publish finalized software packages, similarly as Docker Hub images.
* The **local registry**, which stores packages being developed (`dev`), or fetched from the remote registry (`third_party`) to be used locally.

Additionally, when running agents or service deployments locally, we recommend that you fetch them outside the local registry. This is because the framework will download any required component (or create auxiliary files and folders) within the **runtime folders** of agents and services. Therefore, we recommend that you keep the copies on the local registry clean to avoid publishing unintended files (e.g., private keys) on the remote registry.

This is roughly how your workspace should look like:

<figure markdown>
![](../images/workspace.svg)
</figure>

!!! tip

    You can override the default registry in use (set up with `autonomy init`) for a particular command through the flags `--registry-path` and `--local`. For example, if the framework was initialized with the remote registry, the following command will fetch a runtime folder for the `hello_world` agent from the remote registry:

    ```bash
    autonomy fetch valory/hello_world:0.1.0:bafybeictwjngvb7qon4qisl3q4ztfzvj5pi26zhmpm2oqg6xx6vbz6jrya
    ```

    On the other hand, if you want to fetch the copy stored in your local registry, then you can use:
    ```bash
    autonomy --registry-path=./packages fetch valory/hello_world:0.1.0 --local
    ```

## The Dev template

For convenience, we provide a **Dev template** repository that you can fork and clone for your Open Autonomy projects, and use it as your workspace folder:

<figure markdown>
[ https://github.com/valory-xyz/dev-template ](https://github.com/valory-xyz/dev-template)
</figure>

The **Dev template** comes with:

* a preconfigured Pipenv environment with required dependencies,
* an empty local registry,
* a number of preconfigured linters via [Tox](https://tox.wiki/en/latest/).

## Populate the local registry for the guides

If you plan to follow the guides in the next sections, you need to populate the local registry with a number of [packages shipped with the framework](../package_list.md). To do so, edit the local registry index file (`./packages/packages.json`) and ensure that it has the following `third_party` entries:

```json
{
    "dev": {
    },
    "third_party": {
        "service/valory/hello_world/0.1.0": "bafybeibp2iiojzyykcbkadqdszd35laq2ub34eovyghrsr33t2vrxmk2r4",
        "agent/valory/hello_world/0.1.0": "bafybeictwjngvb7qon4qisl3q4ztfzvj5pi26zhmpm2oqg6xx6vbz6jrya",
        "connection/valory/abci/0.1.0": "bafybeiclexb6cnsog5yjz2qtvqyfnf7x5m7tpp56hblhk3pbocbvgjzhze",
        "connection/valory/http_client/0.23.0": "bafybeih5vzo22p2umhqo52nzluaanxx7kejvvpcpdsrdymckkyvmsim6gm",
        "connection/valory/ipfs/0.1.0": "bafybeihndk6hohj3yncgrye5pw7b7w2kztj3avby5u5mfk2fpjh7hqphii",
        "connection/valory/ledger/0.19.0": "bafybeic3ft7l7ca3qgnderm4xupsfmyoihgi27ukotnz7b5hdczla2enya",
        "contract/valory/service_registry/0.1.0": "bafybeicbxmbzt757lbmyh6762lrkcrp3oeum6dk3z7pvosixasifsk6xlm",
        "protocol/open_aea/signing/1.0.0": "bafybeihv62fim3wl2bayavfcg3u5e5cxu3b7brtu4cn5xoxd6lqwachasi",
        "protocol/valory/abci/0.1.0": "bafybeiaqmp7kocbfdboksayeqhkbrynvlfzsx4uy4x6nohywnmaig4an7u",
        "protocol/valory/acn/1.1.0": "bafybeidluaoeakae3exseupaea4i3yvvk5vivyt227xshjlffywwxzcxqe",
        "protocol/valory/contract_api/1.0.0": "bafybeidgu7o5llh26xp3u3ebq3yluull5lupiyeu6iooi2xyymdrgnzq5i",
        "protocol/valory/http/1.0.0": "bafybeifugzl63kfdmwrxwphrnrhj7bn6iruxieme3a4ntzejf6kmtuwmae",
        "protocol/valory/ipfs/0.1.0": "bafybeiftxi2qhreewgsc5wevogi7yc5g6hbcbo4uiuaibauhv3nhfcdtvm",
        "protocol/valory/ledger_api/1.0.0": "bafybeihdk6psr4guxmbcrc26jr2cbgzpd5aljkqvpwo64bvaz7tdti2oni",
        "protocol/valory/tendermint/0.1.0": "bafybeig4mi3vmlv5zpbjbfuzcgida6j5f2nhrpedxicmrrfjweqc5r7cra",
        "skill/valory/abstract_abci/0.1.0": "bafybeihat4giyc4bz6zopvahcj4iw53356pbtwfn7p4d5yflwly2qhahum",
        "skill/valory/abstract_round_abci/0.1.0": "bafybeih3enhagoql7kzpeyzzu2scpkif6y3ubakpralfnwxcvxexdyvy5i",
        "skill/valory/hello_world_abci/0.1.0": "bafybeiagjdjp5ut4svjyitsrkr4l7gosfefx5ebphrlkaa6a765fwuljai",
        "connection/valory/p2p_libp2p_client/0.1.0": "bafybeid3xg5k2ol5adflqloy75ibgljmol6xsvzvezebsg7oudxeeolz7e"
    }
}
```

Execute the following command after updating the `packages.json` file:

```bash
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.
