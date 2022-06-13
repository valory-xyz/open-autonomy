
# Release Process from develop to main

1. Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit). Make sure you have a clean develop virtual environment. 
   
2. Determine the next `open-autonomy` version 
   Create new release branch named "feature/release-{new-version}, switch to this branch"
   Update the version in `autonomy/__version__.py`. Commit if satisfied.

3. [CURRENTLY SKIPPED] Bump all the packages to their latest versions by running `python scripts/update_package_versions.py`.

4. [CURRENTLY SKIPPED] Check the package upgrades are correct by running `python -m aea.cli check-packages` and `python scripts/check_package_versions_in_docs.py`. Commit if satisfied.

5. [CURRENTLY SKIPPED] Check the docs are up-to-date by running `python scripts/generate_api_docs.py` and `python scripts/check_doc_links.py`. Ensure all links are configured `mkdocs serve`. Commit if satisfied.

6. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

7. Run spell checker `./scripts/spell-check.sh`. Run `pylint --disable all --enable spelling ...`. Commit if required.

8. Open PRs and merge into develop. Then open develop to main PR and merge it.

9. Tag version on main.

10. Pull main, make a clean environment (`pipenv --rm` and `pipenv --python 3.10` and `pipenv shell`) and create distributions: `make dist`.

11. Publish to PyPI with twine (`pip install twine`): `twine upload dist/*`. Optionally, publish to Test-PyPI with twine:
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`.

12. Make clean environment and install release from PyPI: `pip install open-autonomy --no-cache`.

13. [CURRENTLY SKIPPED] Release packages into registry: `python scripts/deploy_to_registry.py`. If necessary, run it several times until all packages are updated.

14. [CURRENTLY SKIPPED] The docker images are updated via CI.

If something goes wrong and only needs a small fix do `LAST_VERSION.post1` as version, apply fixes, push again to PyPI.