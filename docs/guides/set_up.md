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
    autonomy fetch valory/hello_world:0.1.0:bafybeih36hdmv5gcle4ghtpxih5g3ymebvgo7sa2fqbco5cida3kxltayy
=======
    autonomy fetch valory/hello_world:0.1.0:bafybeih36hdmv5gcle4ghtpxih5g3ymebvgo7sa2fqbco5cida3kxltayy
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
        "service/valory/hello_world/0.1.0": "bafybeiejpoulfeqn6fk6bpbbyy6c5wkvwb6qdg3irpgbx45kxpy2xeobzu",
        "agent/valory/hello_world/0.1.0": "bafybeih36hdmv5gcle4ghtpxih5g3ymebvgo7sa2fqbco5cida3kxltayy",
        "connection/valory/abci/0.1.0": "bafybeihofnsokowicviac6yz3uhur52l3mf54s2hz4i2je5ie4vlruouga",
        "connection/valory/http_client/0.23.0": "bafybeidykl4elwbcjkqn32wt5h4h7tlpeqovrcq3c5bcplt6nhpznhgczi",
        "connection/valory/ipfs/0.1.0": "bafybeiatjutuiav7oxl4hszy3oypdwuetr6crjpminush54c5k4nbeciv4",
        "connection/valory/ledger/0.19.0": "bafybeicgfupeudtmvehbwziqfxiz6ztsxr5rxzvalzvsdsspzz73o5fzfi",
        "contract/valory/service_registry/0.1.0": "bafybeibdy55edqs3djptv77ljkmbf6m3zizhutmvwgj3hpsagvmzhr4jbm",
        "protocol/open_aea/signing/1.0.0": "bafybeibqlfmikg5hk4phzak6gqzhpkt6akckx7xppbp53mvwt6r73h7tk4",
        "protocol/valory/abci/0.1.0": "bafybeig3dj5jhsowlvg3t73kgobf6xn4nka7rkttakdb2gwsg5bp7rt7q4",
        "protocol/valory/acn/1.1.0": "bafybeignmc5uh3vgpuckljcj2tgg7hdqyytkm6m5b6v6mxtazdcvubibva",
        "protocol/valory/contract_api/1.0.0": "bafybeidv6wxpjyb2sdyibnmmum45et4zcla6tl63bnol6ztyoqvpl4spmy",
        "protocol/valory/http/1.0.0": "bafybeifyoio7nlh5zzyn5yz7krkou56l22to3cwg7gw5v5o3vxwklibhty",
        "protocol/valory/ipfs/0.1.0": "bafybeic72ncgqbzoz2guj4p4yjqulid7mv6yroeh65hxznloamoveeg7hq",
        "protocol/valory/ledger_api/1.0.0": "bafybeibo4bdtcrxi2suyzldwoetjar6pqfzm6vt5xal22ravkkcvdmtksi",
        "protocol/valory/tendermint/0.1.0": "bafybeicusvezoqlmyt6iqomcbwaz3xkhk2qf3d56q5zprmj3xdxfy64k54",
        "skill/valory/abstract_abci/0.1.0": "bafybeiff2dqnkeorf343fmb3547fhiznvdw4ewbwl4rqluek2cv6ibl5hi",
        "skill/valory/abstract_round_abci/0.1.0": "bafybeihlcferdpjhcorbrgp3zplikxkuxmlx3x7mc4g5sjxxm2mgzryfia",
        "skill/valory/hello_world_abci/0.1.0": "bafybeidzbbkgq7tmy7dot3kn6nmormujcdqukviwvmb6vwr2enuxlusmoe",
        "connection/valory/p2p_libp2p_client/0.1.0": "bafybeidwcobzb7ut3efegoedad7jfckvt2n6prcmd4g7xnkm6hp6aafrva"
    }
}
```

Execute the following command after updating the `packages.json` file:

```bash
autonomy packages sync
```

The framework will fetch components from the remote registry into the local registry.
