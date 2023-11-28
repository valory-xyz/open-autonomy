To bump a service to the latest version of open-autonomy follow these steps

1. Bump open-autonomy and relevant dependencies to the desired version in `tox.ini`, `pipfile/pyproject.toml` and `packages`. You can also use [this](https://github.com/valory-xyz/open-autonomy/blob/main/scripts/bump.py) script to bump the dependencies in your repository.
2. Create a new virtual environment and install the latest dependencies 
3. Perform sync and lock the packages
   > autonomy packages sync --update-packages --source `valory-xyz/open-autonomy:<OPEN_AUTONOMY_VERSION>` --source `valory-xyz/open-aea:<OPEN_AEA_VERSION>`

   > autonomy packages lock
