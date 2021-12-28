.PHONY: clean
clean: clean-build clean-pyc clean-test clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	rm -fr Pipfile.lock

.PHONY: clean-docs
clean-docs:
	rm -fr site/

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.DS_Store' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	rm -fr .tox/
	rm -f .coverage
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;
	rm -fr coverage.xml
	rm -fr htmlcov/
	rm -fr .hypothesis
	rm -fr .pytest_cache
	rm -fr .mypy_cache/
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +

.PHONY: lint
lint:
	black aea_consensus_algorithms packages/valory scripts tests
	isort aea_consensus_algorithms packages/valory scripts tests
	flake8 aea_consensus_algorithms packages/valory scripts tests
	vulture aea_consensus_algorithms scripts/whitelist.py
	darglint aea_consensus_algorithms scripts packages/valory/agents packages/valory/connections packages/valory/contracts packages/valory/skills tests

.PHONY: pylint
pylint:
	pylint -j4 aea_consensus_algorithms packages/valory scripts

.PHONY: security
security:
	bandit -r aea_consensus_algorithms packages
	bandit -s B101 -r tests scripts
	safety check -i 37524 -i 38038 -i 37776 -i 38039 -i 39621 -i 40291 -i 39706 -i 41002 -i 40622

.PHONY: static
static:
	mypy aea_consensus_algorithms packages/valory scripts --disallow-untyped-defs
	mypy tests --disallow-untyped-defs

.PHONY: package_checks
package_checks:
	python scripts/generate_ipfs_hashes.py --check --vendor valory
	python scripts/check_packages.py --vendor valory

.PHONY: hashes
hashes:
	python scripts/generate_ipfs_hashes.py --vendor valory

.PHONY: docs
docs:
	mkdocs build --clean

.PHONY: common_checks
common_checks: security misc_checks lint static docs

.PHONY: test
test:
	pytest -rfE --doctest-modules aea_consensus_algorithms tests/ --cov=aea_consensus_algorithms --cov-report=html --cov=packages/valory --cov-report=xml --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: checks
checks:
	make clean \
	&& make static \
	&& make lint \
	&& make pylint \
	&& make hashes \
	&& make test-sub-p tdir=skills/test_price_estimation_abci/ dir=skills.price_estimation_abci \
	&& make test-sub-p tdir=skills/test_liquidity_provision/ dir=skills.liquidity_provision

# how to use:
#
#     make test-sub-p tdir=$TDIR dir=$DIR
#
# where:
# - TDIR is the path to the test module/directory (but without the leading "test_")
# - DIR is the *dotted* path to the module/subpackage whose code coverage needs to be reported.
#
# For example, to run the ABCI connection tests (in tests/test_connections/test_abci.py)
# and check the code coverage of the package packages.valory.connections.abci:
#
#     make test-sub-p tdir=connections/test_abci.py dir=connections.abci
#
# Or, to run tests in tests/test_skills/test_counter/ directory and check the code coverage
# of the skill packages.valory.skills.counter:
#
#     make test-sub-p tdir=skills/test_counter/ dir=skills.counter
#
.PHONY: test-sub-p
test-sub-p:
	pytest -rfE tests/test_$(tdir) --cov=packages.valory.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;


.PHONY: test-all
test-all:
	tox

.PHONY: install
install: clean
	python3 setup.py install

.PHONY: dist
dist: clean
	python setup.py sdist
	WIN_BUILD_WHEEL=1 python setup.py bdist_wheel --plat-name=win_amd64
	WIN_BUILD_WHEEL=1 python setup.py bdist_wheel --plat-name=win32
	python setup.py bdist_wheel --plat-name=manylinux1_x86_64
	python setup.py bdist_wheel --plat-name=manylinux2014_aarch64
	python setup.py bdist_wheel --plat-name=macosx_10_9_x86_64

h := $(shell git rev-parse --abbrev-ref HEAD)

.PHONY: release_check
release:
	if [ "$h" = "main" ];\
	then\
		echo "Please ensure everything is merged into main & tagged there";\
		pip install twine;\
		twine upload dist/*;\
	else\
		echo "Please change to main branch for release.";\
	fi

v := $(shell pip -V | grep virtualenvs)

.PHONY: new_env
new_env: clean
	if [ ! -z "$(which svn)" ];\
	then\
		echo "The development setup requires SVN, exit";\
		exit 1;\
	fi;\

	if [ -z "$v" ];\
	then\
		pipenv --rm;\
		pipenv --python 3.8;\
		pipenv install --dev --skip-lock;\
		pipenv run pip install -e .[all];\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi

.PHONY: install_pre_commit
install_pre_commit:
	echo "Installing pre_commit"
	cp scripts/pre-commit .git/hooks/pre-commit