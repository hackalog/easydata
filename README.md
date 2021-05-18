[![Build Status](https://travis-ci.org/hackalog/cookiecutter-easydata.svg?branch=master)](https://travis-ci.org/hackalog/cookiecutter-easydata)
[![CircleCI](https://circleci.com/gh/hackalog/easydata.svg?style=shield)](https://app.circleci.com/pipelines/github/hackalog/easydata)
[![Coverage Status](https://coveralls.io/repos/github/hackalog/cookiecutter-easydata/badge.svg?branch=master)](https://coveralls.io/github/hackalog/cookiecutter-easydata?branch=master)
[![Documentation Status](https://readthedocs.org/projects/cookiecutter-easydata/badge/?version=latest)](https://cookiecutter-easydata.readthedocs.io/en/latest/?badge=latest)

# EasyData

_A python framework and git template for data scientists, teams, and workshop organizers
aimed at making your data science **reproducible**_

For most of us, data science is 5% science, 60% data cleaning, and 35%
IT hell.  Easydata focuses the 95% by helping you deliver
* reproducible python environments,
* reproducible datasets, and
* reproducible workflows

In other words, Easydata is a template, library, and workflow that lets you **get up and running with your data science analysis, quickly and reproducibly**.

## What is Easydata?

Easydata is a framework for building custom data science git repos that provides:
* An **prescribed workflow** for collaboration, storytelling,
* A **python framework** to support this workflow
* A **makefile wrapper** for conda and pip environment management
* prebuilt **dataset recipes**, and
* a vast library of training materials and documentation around doing reproducible data science.

Easydata is **not**
* an ETL tooklit
* A data analysis pipeline
* a containerization solution, or
* a prescribed data format.


### Requirements to use this framework:
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

    cookiecutter https://github.com/hackalog/easydata


### The resulting directory structure
------------

The directory structure of your new project looks like this:


* `LICENSE`
    * Terms of use for this repo
* `Makefile`
    * top-level makefile. Type `make` for a list of valid commands
* `Makefile.include`
    * Global includes for makefile routines. Included by `Makefile`.
* `Makefile.env`
    * Command for maintaining reproducible conda environment. Included by `Makefile`.
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
* `environment.yml`
    * The user-readable YAML file for reproducing the conda/pip environment.
* `environment.(platform).lock.1yml`
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


## Credits and Thanks
* Early versions of Easydata were based on the excellent
[cookiecutter-data-science](http://drivendata.github.io/cookiecutter-data-science/)
template.
* Thanks to the [Tutte Institute](https://github.com/TutteInstitute) for supporting the development of this framework.
