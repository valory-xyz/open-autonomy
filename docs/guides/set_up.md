The purpose of this guide is to set up your system to work with the {{open_autonomy}} framework. All the remaining guides assume that you have followed these set up instructions.

## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.7` (recommended `>= 3.10`)
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
<<<<<<< HEAD
    autonomy fetch valory/hello_world:0.1.0:bafybeifcyanng2ppdhpsovworx2q7fbhrzrjlueqfzhlixbv7mua4lze4u
=======
    autonomy fetch valory/hello_world:0.1.0:bafybeifcyanng2ppdhpsovworx2q7fbhrzrjlueqfzhlixbv7mua4lze4u
>>>>>>> fix/send-none-on-no-message
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
        "service/valory/hello_world/0.1.0": "bafybeihby3xgza5zw5xtrpkkkj5amt446ya3jm7vikdszxc4bnmpaubj5a",
        "agent/valory/hello_world/0.1.0": "bafybeifcyanng2ppdhpsovworx2q7fbhrzrjlueqfzhlixbv7mua4lze4u",
        "connection/valory/abci/0.1.0": "bafybeif4je7jk6r3cv2pjfkk5qmobyhwuvv2oyvjozttcvpapnb3v4zome",
        "connection/valory/http_client/0.23.0": "bafybeifdb5urioonbzlpqptu4ee76utmzq6tli3cpqnlyez7fn4jag2mci",
        "connection/valory/ipfs/0.1.0": "bafybeial2bbx5qvlpuwhpbb47yjd65kenwcth65u2bqelvc2omzisue3eq",
        "connection/valory/ledger/0.19.0": "bafybeibeb2zpyoxcvlhp5xtx7vr7nythn3cfwfmzentocupdcbbx22xklm",
        "contract/valory/service_registry/0.1.0": "bafybeiesh4be5q5httbnwfd5mphojwg2mfbhspityy3p75chcv3fkngyuy",
        "protocol/open_aea/signing/1.0.0": "bafybeifuxs7gdg2okbn7uofymenjlmnih2wxwkym44lsgwmklgwuckxm2m",
        "protocol/valory/abci/0.1.0": "bafybeigootsvqpk6th5xpdtzanxum3earifrrezfyhylfrit7yvqdrtgpe",
        "protocol/valory/acn/1.1.0": "bafybeibifwnyxae7ar3mpdqgu3mv3u5db4noinpi2pj5dqt7velwt7exqy",
        "protocol/valory/contract_api/1.0.0": "bafybeiezsmj4kvyyscy2s3rftennbyau5cfqn2hb2bk3cj6gptbmmiava4",
        "protocol/valory/http/1.0.0": "bafybeianlbknceiznl2rhc7xq23sb6jb2zoe7dnnzof4ccjvo7wcuyuk3q",
        "protocol/valory/ipfs/0.1.0": "bafybeibjzhsengtxfofqpxy6syamplevp35obemwfp4c5lhag3v2bvgysa",
        "protocol/valory/ledger_api/1.0.0": "bafybeidk4nn7hs7ttq3kwxmqd6h5qjhxp5skkbarpip6csekccxchpn42e",
        "protocol/valory/tendermint/0.1.0": "bafybeidjqmwvgi4rqgp65tbkhmi45fwn2odr5ecezw6q47hwitsgyw4jpa",
        "skill/valory/abstract_abci/0.1.0": "bafybeife3lndiy6b6zreqlgwiwoyufdcu2zqov3fdkiqqzefkwe4iqddn4",
        "skill/valory/abstract_round_abci/0.1.0": "bafybeicrvq7kxyzaxrhgtmjyfeuhgjpvqz7ukdx4nsjdrql5yqluetml2i",
        "skill/valory/hello_world_abci/0.1.0": "bafybeicxbrqlems7egvvap7hfymjpvblwyexolluk3blpl6vgnndqs6dlm",
        "connection/valory/p2p_libp2p_client/0.1.0": "bafybeierggvxlpnsowctmfc5brlk26bhbexxregi7udxnpfhzpjf5ufaeq"
    }
}
```

Execute the following command after updating the `packages.json` file:

```bash
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.
