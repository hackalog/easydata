# Cookiecutter EasyData

_A flexible toolkit for doing and sharing reproducible data science._

EasyData started life as an experimental fork of
[cookiecutter-data-science](http://drivendata.github.io/cookiecutter-data-science/)
where we could try out ideas before proposing them as fixes to the upstream branch. It has grown into its own toolkit for implementing a reproducible data science workflow, and is the basis of our [Bus Number](https://github.com/hackalog/bus_number/) tutorial on **Reproducible Data Science**.

### Tutorial
For a tutorial on making use of this framework, visit:
  https://github.com/hackalog/bus_number/


### Requirements to use this cookiecutter template:
 - anaconda (or miniconda)

 - python3.6+ (we use f-strings. So should you)

 - [Cookiecutter Python package](http://cookiecutter.readthedocs.org/en/latest/installation.html) >= 1.4.0: This can be installed with pip by or conda depending on how you manage your Python packages:

``` bash
$ pip install cookiecutter
```

or

``` bash
$ conda config --add channels conda-forge
$ conda install cookiecutter
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
* `setup.py`
    * Turns contents of `MODULE_NAME` into a
    pip-installable python module  (`pip install -e .`) so it can be
    imported in python code
* `MODULE_NAME`
    * Source code for use in this project.
    * `MODULE_NAME/__init__.py`
        * Makes MODULE_NAME a Python module
    * `MODULE_NAME/data`
        * Scripts to fetch or generate data. In particular:
        * `MODULE_NAME/data/make_dataset.py`
            * Run with `python -m MODULE_NAME.data.make_dataset fetch`
            or  `python -m MODULE_NAME.data.make_dataset process`
    * `MODULE_NAME/analysis`
        * Scripts to turn datasets into output products
    * `MODULE_NAME/models`
        * Scripts to train models and then use trained models to make predictions.
        e.g. `predict_model.py`, `train_model.py`
* `tox.ini`
    * tox file with settings for running tox; see tox.testrun.org


### Installing development requirements
The first time:
```make create_environment```

Subsequent updates:
```make update_environment```

In case you need to delete the environment later:
```conda deactivate
make delete_environment```
