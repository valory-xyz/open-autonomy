
# Release Process from develop to main

1. Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit). Make sure you have a clean develop virtual environment. 
   
2. Determine the next `open-autonomy` version. Create new release branch named `feature/release-{new-version}`, switch to this branch. Update the version in `autonomy/__version__.py`. Commit if satisfied.

3. Determine the next `open-aea-test-autonomyy` version. Update the version in `plugins/aea_test_autonomy/setup.py` and relevant component configurations. Commit if satisfied.

4. [CURRENTLY SKIPPED] Bump all the packages to their latest versions by running `python scripts/update_package_versions.py`.

5. Check the package upgrades are correct by running `autonomy check-packages`. Commit if satisfied.

6. Check the docs are up-to-date by running `python scripts/generate_api_documentation.py`. Ensure all links are configured `mkdocs serve`. Commit if satisfied.

7. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

8. Run spell checker `./scripts/spell-check.sh`. Run `pylint --disable all --enable spelling ...`. Commit if required.

9. Open PRs and merge into develop. Then open develop to main PR and merge it.

10. Tag version on main.

11. Pull main, make a clean environment (`pipenv --rm` and `pipenv --python 3.10` and `pipenv shell`) and create distributions: `make dist`.

12. Publish to PyPI with twine (`pip install twine`): `twine upload dist/*`. Optionally, publish to Test-PyPI with twine:
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`.

12. Repeat 11. for each plugin (use `python setup.py sdist bdist_wheel` instead of `make dist`).

13. Make clean environment and install release from PyPI: `pip install open-autonomy --no-cache`.

14. Release packages into registry: `autonomy init --reset --author valory --ipfs --remote` and `autonomy push-all`. If necessary, run it several times until all packages are updated.

15. Build and tag images for the documentation. `VERSION=TAG-TO-BE-RELEASED make release-images`. Inform DevOps of new release so that these images can be rolled out.

If something goes wrong and only needs a small fix do `LAST_VERSION.post1` as version, apply fixes, push again to PyPI.
