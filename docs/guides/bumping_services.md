To bump a repository containing a service to an updated version of {{open_autonomy}}, follow these steps:

1. Bump the PyPI package `open-autonomy` and any relevant dependency to the desired version in the files
   - `tox.ini`,
   - `Pipfile` (for Pipenv repositories),
   - `pyproject.toml` (for Poetry repositories).

   Also, update any reference of the bumped packages within the `packages` folder. For convenience, we provide [this script](https://github.com/valory-xyz/open-autonomy/blob/main/scripts/bump.py) to help you bump the dependencies to the latest version of {{open_autonomy}}.
2. Create a new virtual environment and install the bumped dependencies.
3. Perform sync and lock the packages:

   ```bash
   autonomy packages sync --update-packages --source `valory-xyz/open-autonomy:<OPEN_AUTONOMY_VERSION>` --source `valory-xyz/open-aea:<OPEN_AEA_VERSION>`
   autonomy packages lock
   ```

   You must use the appropriate version tags for `<OPEN_AUTONOMY_VERSION>` and `<OPEN_AEA_VERSION>`:

   ```bash
   autonomy --version
   aea --version
   ```
