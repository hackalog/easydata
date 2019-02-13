.PHONY: clean data lint requirements sync_data_to_s3 sync_data_from_s3 fetch_data unpack_data predict train test_environment

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = {{ cookiecutter.s3_bucket }}
PROFILE = {{ cookiecutter.aws_profile }}
PROJECT_NAME = {{ cookiecutter.repo_name }}
MODULE_NAME = {{ cookiecutter.module_name }}
PYTHON_INTERPRETER = {{ cookiecutter.python_interpreter }}
VIRTUALENV = {{ cookiecutter.virtualenv }}
CONDA_EXE ?= {{ cookiecutter.conda_path }}

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install or update Python Dependencies
requirements: test_environment environment.lock requirements.lock

requirements.lock: requirements.txt
ifneq (conda, $(VIRTUALENV))
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt
endif

## convert raw datasets into fully processed datasets
data: transform_data

## Fetch, Unpack, and Process raw DataSources
sources: process_sources

fetch_sources:
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.data.make_dataset fetch

unpack_sources:
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.data.make_dataset unpack

process_sources:
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.data.make_dataset process

## Apply Transformations to produce fully processed Datsets
transform_data:
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.data.apply_transforms transformer_list.json

## train / fit / build models
train: models/model_list.json
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.models.train_models model_list.json

## predict / transform / run experiments
predict: models/predict_list.json
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.models.predict_model predict_list.json

## Convert predictions / transforms / experiments into output data
analysis: reports/analysis_list.json
	$(PYTHON_INTERPRETER) -m {{ cookiecutter.module_name }}.analysis.run_analysis analysis_list.json

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Delete all interim (DataSource) files
clean_interim:
	rm -rf data/interim/*

## Delete the raw downloads directory
clean_raw:
	rm -f data/raw/*

## Delete all processed datasets
clean_processed:
	rm -f data/processed/*

## Delete all trained models
clean_models:
	rm -f models/trained/*
	rm -f models/trained_models.json

## Delete all predictions
clean_predictions:
	rm -f models/predictions/*
	rm -f models/predictions.json

clean_workflow:
	rm -f catalog/datasources.json
	rm -f catalog/transformer_list.json
	rm -f models/model_list.json
	rm -f models/predict_list.json
	rm -f models/predictions.json
	rm -f models/trained_models.json
	rm -f reports/analysis_list.json
	rm -f reports/summary_list.json
	rm -f reports/analyses.json
	rm -f reports/summaries.json

## Run all Unit Tests
test:
	cd {{ cookiecutter.module_name }} && pytest --doctest-modules --verbose --cov

## Lint using flake8
lint:
	flake8 {{ cookiecutter.module_name }}

## Upload Data to S3
sync_data_to_s3:
ifeq (default,$(PROFILE))
	aws s3 sync data/ s3://$(BUCKET)/data/
else
	aws s3 sync data/ s3://$(BUCKET)/data/ --profile $(PROFILE)
endif

## Download Data from S3
sync_data_from_s3:
ifeq (default,$(PROFILE))
	aws s3 sync s3://$(BUCKET)/data/ data/
else
	aws s3 sync s3://$(BUCKET)/data/ data/ --profile $(PROFILE)
endif

environment.lock: environment.yml
ifeq (conda, $(VIRTUALENV))
	$(CONDA_EXE) env update -n $(PROJECT_NAME) -f $<
	$(CONDA_EXE) env export -n $(PROJECT_NAME) -f $@
else
	$(error Unsupported Environment `$(VIRTUALENV)`. Use conda)
endif

## Set up python interpreter environment
create_environment:
ifeq (conda,$(VIRTUALENV))
	@echo ">>> Detected conda, creating conda environment."
ifneq ("X$(wildcard ./environment.lock)","X")
	$(CONDA_EXE) env create --name $(PROJECT_NAME) -f environment.lock
else
	@echo ">>> Creating lockfile from $(CONDA_EXE) environment specification."
	$(CONDA_EXE) env create --name $(PROJECT_NAME) -f environment.yml
	$(CONDA_EXE) env export --name $(PROJECT_NAME) -f environment.lock
endif
	@echo ">>> New conda env created. Activate with: 'conda activate $(PROJECT_NAME)'"
else
	$(PYTHON_INTERPRETER) -m pip install -q virtualenv virtualenvwrapper
	@echo ">>> Installing virtualenvwrapper if not already intalled.\nMake sure the following lines are in shell startup file\n\
	export WORKON_HOME=$$HOME/.virtualenvs\nexport PROJECT_HOME=$$HOME/Devel\nsource /usr/local/bin/virtualenvwrapper.sh\n"
	@bash -c "source `which virtualenvwrapper.sh`;mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"
endif

delete_environment:
ifeq (conda,$(VIRTUALENV))
	@echo "Deleting conda environment."
	$(CONDA_EXE) env remove -n $(PROJECT_NAME)
endif


## Test python environment is set-up correctly
test_environment:
ifeq (conda,$(VIRTUALENV))
ifneq (${CONDA_DEFAULT_ENV}, $(PROJECT_NAME))
	$(error Must activate `$(PROJECT_NAME)` environment before proceeding)
endif
endif
	$(PYTHON_INTERPRETER) test_environment.py

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := show-help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: show-help


print-%  : ; @echo $* = $($*)

HELP_VARS := PROJECT_NAME

help-prefix:
	@echo "To get started:"
	@echo "  >>> $$(tput bold)make create_environment$$(tput sgr0)"
	@echo "  >>> $$(tput bold)conda activate $(PROJECT_NAME)$$(tput sgr0)"
	@echo
	@echo "$$(tput bold)Project Variables:$$(tput sgr0)"

show-help: help-prefix $(addprefix print-, $(HELP_VARS))
	@echo
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
