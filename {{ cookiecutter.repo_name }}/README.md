{{cookiecutter.project_name}}
==============================

{{cookiecutter.description}}

GETTING STARTED
---------------

* Create and switch to the  virtual environment:
```
make create_environment
cd {{cookiecutter.project_name}}
conda activate {{cookiecutter.project_name}}
```
* Fetch the raw data and process it into a usable form
```
make data
```
* Explore the notebooks in the `notebooks` directory

Project Organization
------------
* `LICENSE`
* `Makefile`
    * top-level makefile. Type `make` for a list of valid commands
* `README.md`
    * this file
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
* `requirements.txt`
    * (if using pip+virtualenv) The requirements file for reproducing the
    analysis environment, e.g. generated with `pip freeze > requirements.txt`
* `environment.yml`
    * (if using conda) The YAML file for reproducing the analysis environment
* `setup.py`
    * Turns contents of `{{ cookiecutter.module_name }}` into a
    pip-installable python module  (`pip install -e .`) so it can be
    imported in python code
* `{{ cookiecutter.module_name }}`
    * Source code for use in this project.
    * `{{ cookiecutter.module_name }}/__init__.py`
        * Makes {{ cookiecutter.module_name }} a Python module
    * `{{ cookiecutter.module_name }}/data`
        * Scripts to fetch or generate data. In particular:
        * `{{ cookiecutter.module_name }}/data/make_dataset.py`
            * Run with `python -m {{ cookiecutter.module_name }}.data.make_dataset fetch`
            or  `python -m {{ cookiecutter.module_name }}.data.make_dataset process`
    * `{{ cookiecutter.module_name }}/features`
        * Scripts to turn raw data into features for modeling, notably `build_features.py`
    * `{{ cookiecutter.module_name }}/models`
        * Scripts to train models and then use trained models to make predictions.
        e.g. `predict_model.py`, `train_model.py`
    * `{{ cookiecutter.module_name }}/visualization`
        * Scripts to create exploratory and results oriented visualizations; e.g.
        `visualize.py`
* `tox.ini`
    * tox file with settings for running tox; see tox.testrun.org


--------

<p><small>Project derived from the the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>, for experimenting with ideas to improve the template  #cookiecutterdatascience</small></p>
