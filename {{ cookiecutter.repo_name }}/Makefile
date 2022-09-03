# Project Variables
include Makefile.include
# Reproducible Environments
include Makefile.envs

#
# Deprecated
#

.PHONY: requirements

requirements: update_environment
	@$(ECHO) "WARNING: 'make requirements' is deprecated. Use 'make update_environment'"

.PHONY: unfinished
unfinished:
	@$(ECHO) "WARNING: this target is unfinished and may be removed or changed dramatically in future releases"

#
# COMMANDS                                                                      #
#

.PHONY: check_requirements
## Ensure all installation requirements are installed
check_requirements: check_installation
	@$(PYTHON_INTERPRETER) scripts/am_i_ready.py

.PHONY: data
data: datasets

.PHONY: raw
raw: datasources

.PHONY: datasources
datasources: .make.datasources

.make.datasources: catalog/datasources/*
	$(PYTHON_INTERPRETER) -m $(MODULE_NAME).workflow datasources
	#touch .make.datasources

.PHONY: datasets
datasets: .make.datasets

.make.datasets: catalog/datasets/* catalog/transformers/*
	$(PYTHON_INTERPRETER) -m $(MODULE_NAME).workflow datasets
	#touch .make.datasets

.PHONY: clean
## Delete all compiled Python files
clean:
	$(PYTHON_INTERPRETER) scripts/clean.py

.PHONY: clean_interim
clean_interim:
	$(RM) data/interim/*

.PHONY: clean_raw
clean_raw:
	$(RM) data/raw/*

.PHONY: clean_processed
clean_processed:
	$(RM) data/processed/*

.PHONY: clean_workflow
clean_workflow:
	$(RM) catalog/datasources.json
	$(RM) catalog/transformer_list.json

.PHONY: test

## Run all Unit Tests
test: update_environment
	$(SET) LOGLEVEL=DEBUG; pytest --pyargs --doctest-modules --doctest-continue-on-failure --verbose \
		$(if $(CI_RUNNING),--ignore=$(TESTS_NO_CI)) \
		$(MODULE_NAME)

## Run all Unit Tests with coverage
test_with_coverage: update_environment
	$(SET) LOGLEVEL=DEBUG; coverage run -m pytest --pyargs --doctest-modules --doctest-continue-on-failure --verbose \
		$(if $(CI_RUNNING),--ignore=$(TESTS_NO_CI)) \
		$(MODULE_NAME)

.PHONY: lint
## Lint using flake8
lint:
	flake8 $(MODULE_NAME)

.phony: help_update_easydata
help_update_easydata:
	@$(PYTHON_INTERPRETER) scripts/help-update.py

.PHONY: debug
## dump useful debugging information to $(DEBUG_FILE)
debug:
	@$(PYTHON_INTERPRETER) scripts/debug.py $(DEBUG_FILE)


#################################################################################
# PROJECT RULES                                                                 #
#################################################################################


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

HELP_VARS := PROJECT_NAME DEBUG_FILE ARCH PLATFORM

.DEFAULT_GOAL := show-help
.PHONY: show-help
show-help:
	@$(PYTHON_INTERPRETER) scripts/help.py $(foreach v,$(HELP_VARS),-v $(v) $($(v))) $(MAKEFILE_LIST)
