
# Release Process from develop to main

1. Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit). Make sure you have a clean develop virtual environment. 
   
2. Determine the next `open-autonomy` version. Create new release branch named `release/{new-version}`, switch to this branch.

3. Make sure all the dependencies are pinned correctly across all of the file, special `open-aea` and the plugins.

4. Run `autonomy packages sync --update-packages --source valory-xyz/open-aea@v{latest-aea-version}` and `tox -e lock-packages`. Commit if satisfied.

5. Update the version in following files and commit if satisfied.
   - `autonomy/__version__.py`
   - `tests/test_base.py`
   - `deployments/Dockerfiles/autonomy-user/requirements.txt`

6. Determine the next `open-aea-test-autonomy` version. Update the version in `plugins/aea-test-autonomy/setup.py` and relevant component configurations. Commit if satisfied.

7. Check the package upgrades are correct by running `tox -e check-packages`. Commit if satisfied.

8. Check the docs are up-to-date by running `tox -e generate-api-documentation`. Ensure all links are configured and run `tox -e docs`. Commit if satisfied.

9.  Make sure hashes are up-to-date and run `tox -e fix-doc-hashes`.

10. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

11. Run spell checker `tomte check-spelling`. Run `pylint --disable all --enable spelling ...`. Commit if required.

12. Open PRs and merge into develop. Then open develop to main PR and merge it.

13. Tag a release from main.
