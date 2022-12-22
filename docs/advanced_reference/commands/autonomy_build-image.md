Builds the agent image for a service.

The command must be executed within the service directory. That is, a directory containing the service configuration file (`service.yaml`). Labels for images generated using this command will follow the format `valory/oar-<PUBLIC_ID>`.

To build an image for a specific agent without fetching a service, run
```bash
autonomy build-image PUBLIC_ID_OR_HASH
```
where `PUBLIC_ID_OR_HASH` refers to the agent public ID or hash as stored in a local or remote repository.

## Usage

```bash
autonomy build-image [OPTIONS] [PUBLIC_ID_OR_HASH]
```

## Options
```
--service-dir PATH
```
:   Path to service directory.

```
--version TEXT
```
:   Specify tag version for the image.

```
--dev
```
:   Build development image.

```
--pull
```
:   Pull latest dependencies.

```
--help
```
:   Show the help message and exit.


## Examples

```bash
autonomy build-image --service-dir /my_service
```

Builds the agent images for the service located in the directory `my_service`.
