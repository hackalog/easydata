{{cookiecutter.project_name}}
==============================
_Author: {{ cookiecutter.author_name }}_

{{cookiecutter.description}}

This repo is build on the cookiecutter-easydata template and workflow for making it easy to share your work with others and
to build on the work of others. This includes:

* managing conda environments in a consistent and reproducible way,
* built in dataset management (including tracking of licenses),
* pre-established project structure,
* workflows and conventions for contributing notebooks and other code.

REQUIREMENTS
------------
* Make
* conda >= 4.8 (via Anaconda or Miniconda)
* Git

GETTING STARTED
---------------
### Git Configuration and Checking Out the Repo

If you haven't yet done so, please follow the instrucitons
in [Setting up git and Checking Out the Repo](framework-docs/git-configuration.md) in
order to check-out the code and set-up your remote branches

Note: These instructions assume you are using SSH keys (and not HTTPS authentication) with {{ cookiecutter.upstream_location }}.
If you haven't set up SSH access to {{ cookiecutter.upstream_location }}, see [Configuring SSH Access to {{cookiecutter.upstream_location}}](https://github.com/hackalog/cookiecutter-easydata/wiki/Configuring-SSH-Access-to-Github). This also includes instuctions for using more than one account with SSH keys.

Once you've got your local, `origin`, and `upstream` branches configured, you can follow the instructions in this handy [Git Workflow Cheat Sheet](framework-docs/git-workflow.md) to keep your working copy of the repo in sync with the others.

### Setting up your environment
**WARNING**: If you have conda-forge listed as a channel in your `.condarc` (or any other channels other than defaults), remove it during the course of the workshop. Even better, don't use a `.condarc` for managing channels, as it overrides the `environment.yml` instructions and makes things less reproducible. Make the changes to the `environment.yml` file if necessary. We've had some conda-forge related issues with version conflicts. We also recommend [setting your channel priority to 'strict'](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html) to reduce package incompatibility problems.

Initial setup:

* Make note of the path to your conda binary:
```
   $ which conda
   ~/miniconda3/bin/conda
```
* ensure your `CONDA_EXE` environment variable is set to this value (or edit `Makefile.include` directly)
```
    export CONDA_EXE=~/miniconda3/bin/conda
```
* Create and switch to the virtual environment:
```
cd {{cookiecutter.repo_name}}
make create_environment
conda activate {{cookiecutter.repo_name}}
```

Now you're ready to run `jupyter notebook` and explore the notebooks in the `notebooks` directory.

For more instructions on setting up and maintaining your environment (including how to point your environment at your custom forks and work in progress) see [Setting up and Maintaining your Conda Environment Reproducibly](framework-docs/conda-environments.md).

### Loading Datasets

At this point you will be able to load any of the pre-built datasets by the following set of commands:
```python
from {{ cookiecutter.module_name }}.data import Dataset
ds = Dataset.load("<dataset-name>")
```
Because of licenses and other distribution restrictions, some of the datasets will require a manual dowload step. If so, you will prompted at this point and given instructions for what to do. Some datasets will require local pre-processing. If so, the first time your run the command, you will be executing all of the processing scripts (which can be quite slow).

After the first time, data will loaded from cache on disk which should be fast.

To see which datasets are currently available:
```python
from {{ cookiecutter.module_name }} import workflow
workflow.available_datasets(keys_only=True)
```

Note: sometimes datasets can be quite large. If you want to store your data externally, we recommend symlinking your data directory (that is `{{cookiecutter.repo_name}}/data`) to somewhere with more room.

For more on Datasets, see [Getting and Using Datasets](framework-docs/datasets.md).

### Using Notebooks and Sharing your Work
This repo has been set up in such a way as to make:

* environment management easy and reproducible
* sharing analyses via notebooks easy and reproducible

There are some tricks, hacks, and built in utilities that you'll want to check out: [Using Notebooks for Analysis](framework-docs/notebooks.md).

Here are some best practices for sharing using this repo:

* Notebooks go in the...you guessed it...`notebooks` directory. The naming convention is a number (for ordering), the creator’s initials, and a short - delimited description, e.g. `01-jqp-initial-data-exploration`. Please increment the starting number when creating a new notebook.
* When checking in a notebook, run **Kernel->Restart & Run All** or **Kernel->Restart & Clear Output** and then **Save** before checking it in.
* Put any scripts or other code in the `{{ cookiecutter.module_name }}` module. We suggest you create a directory using the same initials you put in your notebook titles (e.g. `{{ cookiecutter.module_name }}/xyz`) You will be able to import it into your notebooks via `from {{ cookiecutter.module_name }}.xyz import ...`.
* See the Project Organization section below to see where other materials should go, such as reports, figures, and references.

For more on sharing your work, including using git, submitting PRs and the like, see [Sharing your Work](framework-docs/sharing-your-work.md).

### Quick References
* [Setting up and Maintaining your Conda Environment Reproducibly](framework-docs/conda-environments.md)
* [Getting and Using Datasets](framework-docs/datasets.md)
* [Using Notebooks for Analysis](framework-docs/notebooks.md)
* [Sharing your Work](framework-docs/sharing-your-work.md)


Project Organization
------------
* `LICENSE`
* `Makefile`
    * Top-level makefile. Type `make` for a list of valid commands.
* `Makefile.include`
    * Global includes for makefile routines. Included by `Makefile`.
* `Makefile.env`
    * Command for maintaining reproducible conda environment. Included by `Makefile`.
* `README.md`
    * this file
* `catalog`
  * Data catalog. This is where config information such as data sources
    and data transformations are saved.
* `data`
    * Data directory. Often symlinked to a filesystem with lots of space.
    * `data/raw`
        * Raw (immutable) hash-verified downloads.
    * `data/interim`
        * Extracted and interim data representations.
    * `data/processed`
        * The final, canonical data sets ready for analysis.
* `docs`
    * Documentation files for this project.
* `framework-docs`
    * Basic documentation on how to use the framework and workflows associated with this project.
* `notebooks`
    *  Jupyter notebooks. Naming convention is a number (for ordering),
    the creator's initials, and a short `-` delimited description,
    e.g. `1.0-jqp-initial-data-exploration`.
* `references`
    * Data dictionaries, manuals, papers, or other explanatory materials.
* `reports`
    * Generated analysis as HTML, PDF, LaTeX, etc.
    * `reports/figures`
        * Generated graphics and figures to be used in reporting.
* `environment.yml`
    * The YAML file for reproducing the conda/pip environment.
* `setup.py`
    * Turns contents of `{{ cookiecutter.module_name }}` into a
    pip-installable python module  (`pip install -e .`) so it can be
    imported in python code.
* `{{ cookiecutter.module_name }}`
    * Source code for use in this project.
    * `{{ cookiecutter.module_name }}/__init__.py`
        * Makes `{{ cookiecutter.module_name }}` a Python module.
    * `{{ cookiecutter.module_name }}/data`
        * Scripts to fetch or generate data.
    * `{{ cookiecutter.module_name }}/analysis`
        * Scripts to turn datasets into output products.

--------

<p><small>This project was built using <a target="_blank" href="https://github.com/hackalog/cookiecutter-easydata">cookiecutter-easydata</a>, a python template aimed at making your data science workflow reproducible.</small></p>
