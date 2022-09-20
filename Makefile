OPEN_AEA_REPO_PATH := "${OPEN_AEA_REPO_PATH}"
DEPLOYMENT_TYPE := "${DEPLOYMENT_TYPE}"
SERVICE_ID := "${SERVICE_ID}"
PLATFORM_STR := $(shell uname)

.PHONY: clean
clean: clean-test clean-build clean-pyc clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	find . -type d -name __pycache__ -exec rm -rv {} +
	rm -fr Pipfile.lock
	rm -rf plugins/*/build
	rm -rf plugins/*/dist

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
	rm -fr .hypothesis/
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
	gitleaks detect --report-format json --report-path leak_report

# generate abci docstrings
# check copyright
# generate latest hashes for updated packages
# generate docs for updated packages
# fix hashes in docs
.PHONY: generators
generators:
	tox -e abci-docstrings
	tox -e fix-copyright
	python -m autonomy.cli hash all
	python -m autonomy.cli packages lock
	tox -e generate-api-documentation
	tox -e fix-doc-hashes

.PHONY: common-checks-1
common-checks-1:
	tox -p -e check-copyright -e check-hash -e check-packages

.PHONY: common-checks-2
common-checks-2:
	tox -e check-api-docs
	tox -e check-abci-docstrings
	tox -e check-abciapp-specs
	tox -e check-handlers
	tox -e check-doc-links-hashes

.PHONY: docs
docs:
	mkdocs build --clean --strict

.PHONY: test
test:
	pytest -rfE --doctest-modules autonomy tests/ --cov=autonomy --cov-report=html --cov=packages/valory --cov-report=xml --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: all-checks
all-checks: clean formatters code-checks security generators common-checks-1 common-checks-2

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
	python setup.py bdist_wheel

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
		pipenv --clear;\
		pipenv --python 3.10;\
		pipenv install --dev --skip-lock;\
		pipenv run pip install -e .[all];\
		pipenv run pip install --no-deps file:plugins/aea-test-autonomy;\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi

.PHONY: install-hooks
install-hooks:
	@echo "Installing pre-push"
	cp scripts/pre-push .git/hooks/pre-push

.PHONY: run-hardhat
run-hardhat:
	docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0

protolint_install:
	GO111MODULE=on GOPATH=~/go go get -u -v github.com/yoheimuta/protolint/cmd/protolint@v0.27.0

protolint_install_win:
	powershell -command '$$env:GO111MODULE="on"; go install github.com/yoheimuta/protolint/cmd/protolint@v0.27.0'

teardown-docker-compose:
	cd abci_build/ && \
		docker-compose kill && \
		docker-compose down && \
		echo "Deployment torndown!" && \
		exit 0
	echo "Failed to teardown deployment!"
	exit 1

teardown-kubernetes:
	if [ "${VERSION}" = "" ];\
	then\
		echo "Ensure you have exported a version to teardown!";\
		exit 1
	fi
	kubectl delete ns ${VERSION}
	echo "Done!"

.PHONY: fix-abci-app-specs
fix-abci-app-specs:
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.apy_estimation_abci.rounds.APYEstimationAbciApp packages/valory/skills/apy_estimation_abci/fsm_specification.yaml || (echo "Failed to check apy_estimation_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.apy_estimation_chained_abci.composition.APYEstimationAbciAppChained packages/valory/skills/apy_estimation_chained_abci/fsm_specification.yaml || (echo "Failed to check apy_estimation_chained_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.liquidity_provision_abci.composition.LiquidityProvisionAbciApp packages/valory/skills/liquidity_provision_abci/fsm_specification.yaml || (echo "Failed to check liquidity_provision_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.liquidity_rebalancing_abci.rounds.LiquidityRebalancingAbciApp packages/valory/skills/liquidity_rebalancing_abci/fsm_specification.yaml || (echo "Failed to check liquidity_rebalancing_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.oracle_abci.composition.OracleAbciApp packages/valory/skills/oracle_abci/fsm_specification.yaml || (echo "Failed to check oracle_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.oracle_deployment_abci.rounds.OracleDeploymentAbciApp packages/valory/skills/oracle_deployment_abci/fsm_specification.yaml || (echo "Failed to check oracle_deployment_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.price_estimation_abci.rounds.PriceAggregationAbciApp packages/valory/skills/price_estimation_abci/fsm_specification.yaml || (echo "Failed to check price_estimation_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp packages/valory/skills/registration_abci/fsm_specification.yaml || (echo "Failed to check registration_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.reset_pause_abci.rounds.ResetPauseABCIApp packages/valory/skills/reset_pause_abci/fsm_specification.yaml || (echo "Failed to check reset_pause_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.safe_deployment_abci.rounds.SafeDeploymentAbciApp packages/valory/skills/safe_deployment_abci/fsm_specification.yaml || (echo "Failed to check safe_deployment_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.simple_abci.rounds.SimpleAbciApp packages/valory/skills/simple_abci/fsm_specification.yaml || (echo "Failed to check simple_abci consistency" && exit 1)
	python -m autonomy.cli analyse abci generate-app-specs packages.valory.skills.transaction_settlement_abci.rounds.TransactionSubmissionAbciApp packages/valory/skills/transaction_settlement_abci/fsm_specification.yaml || (echo "Failed to check transaction_settlement_abci consistency" && exit 1)
	echo "Successfully validated abcis!"


AEA_AGENT_HELLO_WORLD:=valory/hello_world:latest:$(shell cat packages/packages.json | grep "agent/valory/hello_world" | cut -d "\"" -f4 )
AEA_AGENT_ORACLE:=valory/oracle:latest:$(shell cat packages/packages.json | grep "agent/valory/oracle" | cut -d "\"" -f4 )
AEA_AGENT_APY_ESTIMATION:=valory/apy_estimation:latest:$(shell cat packages/packages.json | grep "agent/valory/apy_estimation" | cut -d "\"" -f4 )
release-images:
	export AEA_AGENT_ORACLE=${AEA_AGENT_ORACLE}
	export AEA_AGENT_APY_ESTIMATION=${AEA_AGENT_APY_ESTIMATION}
	export AEA_AGENT=${AEA_AGENT_HELLO_WORLD}
	skaffold build -p release --cache-artifacts=false && skaffold build -p release-latest
	