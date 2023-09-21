The purpose of this guide is to set up your system to work with the {{open_autonomy}} framework. All the remaining guides assume that you have followed these set up instructions.

## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.8` (recommended `>= 3.10`)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation/) `>=2021.x.xx`
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Additionally, if you wish to deploy your service in a Kubernetes cluster:

- [Kubernetes CLI](https://kubernetes.io/docs/tasks/tools/)
- [minikube](https://minikube.sigs.k8s.io/docs/)

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

2. **Install the {{open_autonomy}} framework:**

    ```bash
    pip install open-autonomy[all]
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
    autonomy fetch valory/hello_world:0.1.0:bafybeic5gs6qausrb3xgam4ighqvir7kf2q3wyzw2m5r4xlitzs5mdbcqi
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
        "service/valory/hello_world/0.1.0": "bafybeig3x2f47ykckvyfubfl2kav7ymhfpqxuxv2xe52spxhb324jdnoj4",
        "agent/valory/hello_world/0.1.0": "bafybeic5gs6qausrb3xgam4ighqvir7kf2q3wyzw2m5r4xlitzs5mdbcqi",
        "connection/valory/abci/0.1.0": "bafybeibrbl3zhhknmyb2n7qrftnmrsctyd23ugqsiztv3gpy6jcczgtwvm",
        "connection/valory/http_client/0.23.0": "bafybeieoeuy4brzimtnubmokwirhrx27ezls6cdnl5qik4rkykfle3nn2y",
        "connection/valory/ipfs/0.1.0": "bafybeidu3xd6rd5zysv2due2cnrc3sxx5vss2usxwaxxtxxuyha2kuhd3e",
        "connection/valory/ledger/0.19.0": "bafybeigfoz7d7si7s4jehvloq2zmiiocpbxcaathl3bxkyarxoerxq7g3a",
        "contract/valory/service_registry/0.1.0": "bafybeia24syaeq6quzonzjp4tw67kkjhxocr2diy7sxjnujgzurc3oub2a",
        "protocol/open_aea/signing/1.0.0": "bafybeifuxs7gdg2okbn7uofymenjlmnih2wxwkym44lsgwmklgwuckxm2m",
        "protocol/valory/abci/0.1.0": "bafybeigootsvqpk6th5xpdtzanxum3earifrrezfyhylfrit7yvqdrtgpe",
        "protocol/valory/acn/1.1.0": "bafybeiapa5ilsobggnspoqhspftwolrx52udrwmaxdxgrk26heuvl4oooa",
        "protocol/valory/contract_api/1.0.0": "bafybeiasywsvax45qmugus5kxogejj66c5taen27h4voriodz7rgushtqa",
        "protocol/valory/http/1.0.0": "bafybeia5bxdua2i6chw6pg47bvoljzcpuqxzy4rdrorbdmcbnwmnfdobtu",
        "protocol/valory/ipfs/0.1.0": "bafybeibjzhsengtxfofqpxy6syamplevp35obemwfp4c5lhag3v2bvgysa",
        "protocol/valory/ledger_api/1.0.0": "bafybeigsvceac33asd6ecbqev34meyyjwu3rangenv6xp5rkxyz4krvcby",
        "protocol/valory/tendermint/0.1.0": "bafybeidjqmwvgi4rqgp65tbkhmi45fwn2odr5ecezw6q47hwitsgyw4jpa",
        "skill/valory/abstract_abci/0.1.0": "bafybeidt2bxjluqn3xp6mb4v7ml3bx7ka5gn3vx6c5eqfb6i4q4f3p3nr4",
        "skill/valory/abstract_round_abci/0.1.0": "bafybeiebj63bsscvbvj77w2mf2k4juav3yb7vu4omhcckrmf7yoa2xfbae",
        "skill/valory/hello_world_abci/0.1.0": "bafybeifsnc7dj6dvr7urmrdy4z42s56x4ww2s6ncwvfnda753hfao52s54",
        "connection/valory/p2p_libp2p_client/0.1.0": "bafybeihdnfdth3qgltefgrem7xyi4b3ejzaz67xglm2hbma2rfvpl2annq"
    }
}
```

Execute the following command after updating the `packages.json` file:

```bash
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.
