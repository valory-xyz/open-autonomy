OPEN_AEA_REPO_PATH := "${OPEN_AEA_REPO_PATH}"
DEPLOYMENT_TYPE := "${DEPLOYMENT_TYPE}"
DEPLOYMENT_SPEC := "${DEPLOYMENT_SPEC}"

.PHONY: clean
clean: clean-build clean-pyc clean-test clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr deployments/build/
	rm -fr deployments/Dockerfiles/open_aea/packages
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

# isort: fix import orders
# black: format files according to the pep standards
.PHONY: formatters
formatters:
	tox -e isort
	tox -e black

# black-check: check code style
# isort-check: check for import order
# flake8: wrapper around various code checks, https://flake8.pycqa.org/en/latest/user/error-codes.html
# mypy: static type checker
# pylint: code analysis for code smells and refactoring suggestions
# vulture: finds dead code
# darglint: docstring linter
.PHONY: code-checks
code-checks:
	tox -p -e black-check -e isort-check -e flake8 -e mypy -e pylint -e vulture -e darglint

# safety: checks dependencies for known security vulnerabilities
# bandit: security linter
.PHONY: security
security:
	tox -p -e safety -e bandit

# generate latest hashes for updated packages
# generate docs for updated packages
# update copyright headers
.PHONY: generators
generators:
	python scripts/generate_ipfs_hashes.py --vendor valory
	python scripts/generate_api_documentation.py
	python scripts/check_copyright.py

.PHONY: abci-docstrings
abci-docstrings:
	python scripts/generate_abci_docstrings.py

.PHONY: common-checks-1
common-checks-1:
	tox -p -e check-copyright -e check-hash -e check-packages

.PHONY: common-checks-2
common-checks-2:
	tox -e check-api-docs
	tox -e check-abci-docstrings

.PHONY: copyright
copyright:
	python scripts/check_copyright.py

.PHONY: check-copyright
check-copyright:
	tox -e check-copyright

.PHONY: lint
lint:
	black aea_consensus_algorithms packages/valory scripts tests deployments
	isort aea_consensus_algorithms packages/valory scripts tests deployments
	flake8 aea_consensus_algorithms packages/valory scripts tests deployments
	vulture aea_consensus_algorithms scripts/whitelist.py
	darglint aea_consensus_algorithms scripts packages/valory/* tests deployments

.PHONY: pylint
pylint:
	pylint -j4 aea_consensus_algorithms packages/valory scripts deployments


.PHONY: static
static:
	mypy aea_consensus_algorithms packages/valory scripts deployments --disallow-untyped-defs
	mypy tests --disallow-untyped-defs

.PHONY: package_checks
package_checks:
	python scripts/generate_ipfs_hashes.py --check --vendor valory
	python scripts/check_packages.py --vendor valory

.PHONY: hashes
hashes:
	python scripts/generate_ipfs_hashes.py --vendor valory

.PHONY: api-docs
api-docs:
	python scripts/generate_api_documentation.py

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
	&& python scripts/generate_abci_docstrings.py \
	&& make static \
	&& make lint \
	&& make pylint \
	&& make copyright \
	&& make docs \
	&& tox -e check-api-docs \
	&& make hashes \
	&& make security \

.PHONY: test-skill
test-skill:
	make test-sub-p tdir=skills/test_$(skill)/ dir=skills.$(skill)

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

.PHONY: install-hooks
install-hooks:
	@echo "Installing pre-push"
	cp scripts/pre-push .git/hooks/pre-push

.ONESHELL: build-images
build-images:
	sudo make clean
	if [ "${VERSION}" = "" ];\
	then\
		echo "Ensure you have exported a version to build!";\
		exit 1
	fi
	rsync -avu packages/ deployments/Dockerfiles/open_aea/packages
	rsync -avu Pipfile* deployments/Dockerfiles/open_aea
	if [ "${VERSION}" = "dev" ];\
	then\
		echo "building dev images!";\
		skaffold build --build-concurrency=0 --push=false -p dev && exit 0
		exit 1
	fi
	skaffold build --build-concurrency=0 --push=false -p prod && exit 0
	exit 1

.PHONY: run-hardhat
run-hardhat:
	docker run -p 8545:8545 -it valory/consensus-algorithms-hardhat:0.1.0

# if you get following error
# PermissionError: [Errno 13] Permission denied: '/open-aea/build/bdist.linux-x86_64/wheel'
# or similar to PermissionError: [Errno 13] Permission denied: /**/build
# remove build directory from the folder that you got error for
# for example here it should be /path/to/open-aea/repo/build
.PHONY: run-oracle-dev
run-oracle-dev:
	if [ "${OPEN_AEA_REPO_DIR}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'OPEN_AEA_REPO_DIR'"
		exit 1
	fi
	if [ "$(shell ls ${OPEN_AEA_REPO_DIR}/build)" != "" ];\
	then \
		echo "Please remove ${OPEN_AEA_REPO_DIR}/build manually."
		exit 1
	fi
	export VERSION=dev
	make build-images && \
     	python deployments/click_create.py build-deployment --valory-app oracle_hardhat --deployment-type docker-compose --configure-tendermint && \
     	make run-deploy

.PHONY: run-oracle
run-oracle:
	export VERSION=0.1.0
	make build-images && \
	    python deployments/click_create.py build-deployment --valory-app oracle_hardhat --deployment-type docker-compose --configure-tendermint && \
    	make run-deploy

.PHONY: run-deploy
run-deploy:
	cd deployments/build/ && \
	docker-compose up --force-recreate -t 600


.PHONY: run-deployment
run-deployment:
	if [ "${DEPLOYMENT_TYPE}" = "docker-compose" ];\
	then\
		cd deployments/build/ && \
		docker-compose up --force-recreate -t 600
		exit 0
	fi
	if [ "${DEPLOYMENT_TYPE}" = "kubernetes" ];\
	then\
		cd deployments/build/ && \
		kubectl apply -f build.yaml && exit 0
	fi
	echo "Please ensure you have set the environment variable 'DEPLOYMENT_TYPE'"
	exit 1


.PHONY: build-deploy
build-deploy:
	if [ "${DEPLOYMENT_TYPE}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'DEPLOYMENT_TYPE'"
		exit 1
	fi
	if [ "${DEPLOYMENT_SPEC}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'DEPLOYMENT_SPEC'"
		exit 1
	fi
	if [ "${DEPLOYMENT_KEYS}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'DEPLOYMENT_KEYS'"
		exit 1
	fi
	echo "Building deployment for ${DEPLOYMENT_TYPE} ${DEPLOYMENT_KEYS} ${DEPLOYMENT_SPEC}"
	python deployments/click_create.py build-deployment \
	  --deployment-type ${DEPLOYMENT_TYPE} \
	  --keys-file-path ${DEPLOYMENT_KEYS} \
	  --deployment-file-path ${DEPLOYMENT_SPEC} \
	  --configure-tendermint

protolint_install:
	GO111MODULE=on GOPATH=~/go go get -u -v github.com/yoheimuta/protolint/cmd/protolint@v0.27.0
