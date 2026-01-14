Builds the agent blueprint image for an AI agent.

This command builds the Docker runtime images for the agent blueprint defined in an AI agent configuration file `service.yaml`. By default, the command tags the generated images as

```
<author>/oar-<agent_package>:<package_hash>
```

where `<author>` is the author name from the local CLI config (specified with `autonomy init`), `oar` stands for "Open Autonomy Runtime", and `<agent_package>:<package_hash>` is the `PUBLIC_ID` of the agent blueprint. These default tags can be modified using certain options described below.

!!! warning "Important"

    The images are built by fetching the packages from the IFPS registry. Therefore, before running the command, make sure that all the required packages are published on the IPFS registry.

## Usage

```bash
autonomy build-image [OPTIONS] [AGENT_PUBLIC_ID]
```

## Options

`--service-dir PATH`
:   Path to the AI agent directory.

`-e, --extra-dependency DEPENDENCY`

:   Provide extra dependency.

`--version TEXT`
:   Version tag for the image.

`--image-author TEXT`
:   Author name for the image.

`--pull`
:   Pull the latest dependencies when building the image.

`-f, --dockerfile FILE`
:   Specify custom `Dockerfile` for building the agent blueprint

`--help`
:   Show the help message and exit.

## Examples

* Build the runtime image for an AI agent located in the folder `your_ai_agent`:

    ```bash
    autonomy build-image --service-dir /your_ai_agent
    ```

    Or, alternatively:

    ```bash
    cd /your_ai_agent
    autonomy build-image
    ```

* Build the agent blueprint image for a specific AI agent without fetching the AI agent package:

    ```bash
    autonomy build-image <author>/<agent_package>:<package_hash>
    ```

    where `<author>/<package_name>:<package_hash>` is the `PUBLIC_ID` of the agent blueprint.

* Build an agent blueprint image with a custom version tag:

    ```bash
    autonomy build-image <author>/<agent_package>:<package_hash> --version <version>
    ```

    This will tag the image as `<author>/oar-<agent_package>:<version>`.

* Build an agent blueprint image with a custom author name:

    ```bash
    autonomy build-image <author>/<agent_package>:<package_hash> --image-author <custom_author>
    ```

    This will tag the image as `<custom_author>/oar-<agent_package>:<package_hash>`.

* Include extra python packages:

    ```bash
    autonomy build-image ... -e open-aea-ledger-flashbots==2.0.7
    ```

    This will tag the image as `<author>/oar-<agent_package>:<version>`.
