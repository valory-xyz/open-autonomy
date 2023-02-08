The purpose of this guide is to set up your system to work with the {{open_autonomy}} framework. All the remaining guides assume that you have followed these set up instructions.

## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.7` (recommended `>= 3.10`)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Set up

1. Create a workspace folder:

    ```bash
    mkdir my_workspace
    cd my_workspace
    ```

2. Set up the environment. Remember to use the Python version you have installed. Here we are using 3.10 as reference:

    ```bash
    touch Pipfile && pipenv --python 3.10 && pipenv shell
    ```

3. Install the {{open_autonomy}} framework:

    ```bash
    pip install open-autonomy[all]
    ```

4. Initialize the framework to work with the remote [IPFS](https://ipfs.io) registry. This means that when the framework will be fetching a component, it will do so from the [IPFS](https://ipfs.io):

    ```bash
    autonomy init --remote --ipfs
    ```

    !!! info
        The InterPlanetary File System ([IPFS](https://ipfs.io)) is a protocol, hypermedia and file sharing peer-to-peer network for storing and sharing data in a global, distributed file system. {{open_autonomy}} can use components stored in the [IPFS](https://ipfs.io), or stored locally.

5. If required, initialize an empty local registry:

    ```bash
    mkdir packages
    echo '{"dev": {}, "third_party": {}}' > packages/packages.json
    ```

    !!! info
        If you have an already initialized local registry in a path other than `./packages`, you can indicate so using the flag `--registry-path` before a particular command. For example,

        ``` bash
        autonomy --registry-path=~/projects/my_packages <command>
        ```
