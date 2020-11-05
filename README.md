[![Build Status](https://travis-ci.org/hackalog/cookiecutter-easydata.svg?branch=master)](https://travis-ci.org/hackalog/cookiecutter-easydata)

[![Coverage Status](https://coveralls.io/repos/github/hackalog/cookiecutter-easydata/badge.svg?branch=master)](https://coveralls.io/github/hackalog/cookiecutter-easydata?branch=master)

# Cookiecutter EasyData

_A python framework and git gemplate for data scientists, teams, and workshop organizers
aimed at making your data science **reproducible**__

For most of us, data science is 5% science, 60% data cleaning, and 35%
IT hell.  Easydata focuses on delivering
* reproducible python environments,
* reproducible datasets, and
* reproducible workflows
in order to get you up and running with your data science quickly, and reproducibly.

## What is Easydata?

Easydata is a python cookiecutter for building custom data science git repos that provides:
* An **opinionated workflow** for collaboration, storytelling,
* A **python framework** to support this workflow
* A **makefile wrapper** for conda and pip environment management
* prebuilt **dataset recipes**, and
* a vast library of training materials and documentation around doing reproducible data science.

Easydata is **not**
* an ETL tooklit
* A data analysis pipeline
* a containerization solution, or
* a prescribed data format.


### Requirements to use this cookiecutter template:
 - anaconda (or miniconda)
 - python3.6+ (we use f-strings. So should you)
 - [Cookiecutter Python package](http://cookiecutter.readthedocs.org/en/latest/installation.html) >= 1.4.0: This can be installed with pip by or conda depending on how you manage your Python packages:

once you've installed anaconda, you can install the remaining requirements (including cookiecutter) by doing:

```bash
conda create -n easydata python=3
conda activate easydata
python -m pip install -f requirements.txt
```


### To start a new project, run:
------------

    cookiecutter https://github.com/hackalog/cookiecutter-easydata


### The resulting directory structure
------------

The directory structure of your new project looks like this:


* `LICENSE`
* `Makefile`
    * top-level makefile. Type `make` for a list of valid commands
* `README.md`
    * this file
* `catalog`
  * Data catalog. This is where config information such as data sources
    and data transformations are saved
  * `catalog/config.ini`
     * Local Data Store. This configuration file is for local data only, and is never checked into the repo.
* `data`
    * Data directory. often symlinked to a filesystem with lots of space
    * `data/raw`
        * Raw (immutable) hash-verified downloads
    * `data/interim`
        * Extracted and interim data representations
    * `data/processed`
        * The final, canonical data sets for modeling.
* `docs`
    * A default Sphinx project; see sphinx-doc.org for details
* `framework-docs`
    * Markdown documentation for using Easydata
* `models`
    * Trained and serialized models, model predictions, or model summaries
    * `models/trained`
        * Trained models
    * `models/output`
        * predictions and transformations from the trained models
* `notebooks`
    *  Jupyter notebooks. Naming convention is a number (for ordering),
    the creator's initials, and a short `-` delimited description,
    e.g. `1.0-jqp-initial-data-exploration`.
* `references`
    * Data dictionaries, manuals, and all other explanatory materials.
* `reports`
    * Generated analysis as HTML, PDF, LaTeX, etc.
    * `reports/figures`
        * Generated graphics and figures to be used in reporting
    * `reports/tables`
        * Generated data tables to be used in reporting
    * `reports/summary`
        * Generated summary information to be used in reporting
* `environment.yml`
    * (if using conda) The YAML file for reproducing the analysis environment
* `environment.(platform).lock.yml`
    * resolved versions, result of processing `environment.yml`
* `setup.py`
    * Turns contents of `MODULE_NAME` into a
    pip-installable python module  (`pip install -e .`) so it can be
    imported in python code
* `MODULE_NAME`
    * Source code for use in this project.
    * `MODULE_NAME/__init__.py`
        * Makes MODULE_NAME a Python module
    * `MODULE_NAME/data`
        * code to fetch raw data and generate Datasets from them
    * `MODULE_NAME/analysis`
        * code to turn datasets into output products
* `tox.ini`
    * tox file with settings for running tox; see tox.testrun.org


### Installing development requirements
The first time:
```
make create_environment
git init
git add .
git commit -m "initial import"
git branch easydata   # tag for future easydata upgrades
```

Subsequent updates:
```
make update_environment
```

In case you need to delete the environment later:
```
conda deactivate
make delete_environment
```


## History
Early versions of Easydata were based on
[cookiecutter-data-science](http://drivendata.github.io/cookiecutter-data-science/).
