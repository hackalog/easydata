# Setting up and Maintaining your Conda Environment (Reproducibly)

The `{{ cookiecutter.repo_name }}` repo is set up with template code to make managing your conda environments easy and reproducible. Not only will _future you_ appreciate this, but so will anyone else who needs to work with your code after today.

If you haven't yet, configure your conda environment.

**WARNING**: If you have conda-forge listed as a channel in your `.condarc` (or any other channels other than defaults), you may experience great difficulty generating reproducible conda environments.

We recommend you remove conda-forge (and all other non-default channels) from your `.condarc` file and [set your channel priority to 'strict'](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html). You can still use conda-forge (or any other conda channel), just specify it explicitly in your `environment.yml` by prefixing your package name with `channel-name::`; e.g.
```
  - wheel                    # install from the default (anaconda) channel
  - pytorch::pytorch         # install this from the `pytorch` channel
  - conda-forge::tokenizers  # install this from conda-forge
```

## Configuring your python environment
Easydata uses conda to manage python packages installed by both conda **and pip**.

### Adjust your `.condarc`

```
conda config --set channel_priority strict
```
Whenever possible, re-order your channels so that `default` is first.

```
conda config --prepend channels defaults
```

**Note for Jupyterhub Users**: You will need to store your conda environment in your **home directory** so that they wil be persisted across JupyterHub sessions.
```
conda config --prepend envs_dirs ~/.conda/envs   # Store environments in local dir for JupyterHub
```

#### Locating the `conda` binary
Ensure the Makefile can find your conda binary, either by setting the `CONDA_EXE` environment variable, or by modifying `Makefile.include` directly.

First, check if `CONDA_EXE` is already set
```
   >>> export | grep CONDA_EXE
   CONDA_EXE=/Users/your_username/miniconda3/bin/conda
```

If `CONDA_EXE` is not set, you will need to set it manually in `Makefile.include`; i.e.

* Make note of the path to your conda binary. It should be in the `bin` subdirectory of your Anaconda (or miniconda) installation directory:
```
   >>>  which conda         # this will only work if conda is in your PATH, otherwise, verify manually
   ~/miniconda3/bin/conda
```
* ensure your `CONDA_EXE` environment variable is set to this value; i.e.
```
    >>> export CONDA_EXE=~/miniconda3/bin/conda
```
or edit `Makefile.include` directly.

### Create the conda environment
Create and switch to the virtual environment:
```
cd {{ cookiecutter.repo_name }}
make create_environment
conda activate {{ cookiecutter.repo_name }}
make update_environment
```
**Note**: When creating the environment the first time, you really do need to run **both** `make create_environment` and `make update_environment` for the `{{ cookiecutter.module_name }}` module to install correctly.

To activate the environment, simply `conda activate {{ cookiecutter.repo_name }}`

To deactivate it and return to your base environment, use `conda deactivate`

## Maintaining your Python environment

### Updating your conda and pip environments
The `make` commands, `make create_environment` and `make update_environment` are wrappers that allow you to easily manage your conda and pip environments using the `environment.yml` file.

(If you ever forget which `make` command to run, you can run `make` by itself and it will provide a list of commands that are available.)


When adding packages to your python environment, **do not `pip install` or `conda install` directly**. Always edit `environment.yml` and `make update_environment` instead.

Your `environment.yml` file will look something like this:
```
name: {{ cookiecutter.repo_name }}
dependencies:
  - pip
  - pip:
    - -e .  # conda >= 4.4 only
    - python-dotenv>=0.5.1
    - nbval
    - nbdime
    - umap-learn
    - gdown
  - setuptools
  - wheel
  - git>=2.5  # for git worktree template updating
  - sphinx
  - bokeh
  - click
  - colorcet
  - coverage
  - coveralls
  - datashader
  - holoviews
  - matplotlib
  - jupyter
...
```
To add any package available from conda, add it to the end of the list. If you have a PYPI dependency that's not avaible via conda, add it to the list of pip installable dependencies under `  - pip:`.

You can include any `{{ cookiecutter.upstream_location }}` python-based project in the `pip` section via `git+https://{{ cookiecutter.upstream_location }}/<my_git_handle>/<package>`.

In particular, if you're working off of a fork or a work in progress branch of a repo in {{ cookiecutter.upstream_location }} (say, your personal version of <package>), you can change `git+https://{{ cookiecutter.upstream_location }}/<my_git_handle>/<package>` to

* `git+https://{{ cookiecutter.upstream_location }}/<my_git_handle>/<package>.git` to point to the {{cookiecutter.default_branch}} branch of your fork and
* `git+https://{{ cookiecutter.upstream_location }}/<my_git_handle>/<package>.git@<my branch>` to point to a specific branch.

Once you're done your edits, run `make update_environment` and voila, you're updated.

To share your updated environment, check in your `environment.yml` file. (More on this in [Sharing your Work](sharing-your-work.md))

#### Adding packages from other conda channels
Say we want to add a package only available from the `conda-forge` conda channel and not the default conda channel. (The conda channel is what follows `-c` when using `conda install -c my-channel my-package`. Suppose we want to use `make` on windows. Then we need to use `conda-forge` since the default conda channel only has linux and macOS installations of `make`. To normally conda install this, we would use `conda install -c conda-forge make`. **We won't do that here**.

Instead, we add a `channel-order` section that starts with `defaults` and lists the other channels we want to use in the order we want to install from them (note that this is a custom EasyData section to the `environment.yml`). Then we add our package in the dependency list in the form `channel-name::package-name`, for example, `conda-forge::make`.

In this case an updated `environment.yml` file looks like this:
```
name: {{ cookiecutter.repo_name }}
channel-order:
  - defaults
  - conda-forge
dependencies:
  - pip
  - pip:
    - -e .  # conda >= 4.4 only
    - python-dotenv>=0.5.1
    - nbval
    - nbdime
    - umap-learn
    - gdown
  - setuptools
  - wheel
  - git>=2.5  # for git worktree template updating
  - sphinx
  - bokeh
  - click
  - colorcet
  - coverage
  - coveralls
  - datashader
  - holoviews
  - matplotlib
  - jupyter
  - conda-forge::make
...
```


#### Lock files
Now, we'll admit that this workflow isn't perfectly reproducible in the sense that conda still has to resolve versions from the `environment.yml`. To make it more reproducible, running either `make create_environment` or `make update_environment` will generate an `environment.{$ARCH}.lock.yml` (e.g. `environment.i386.lock.yml`). This file keeps a record of the exact environment that is currently installed in your conda environment `{{ cookiecutter.repo_name }}`. If you ever need to reproduce an environment exactly, you can install from the `.lock.yml` file. (Note: These are architecture dependent).

#### Using your conda environment in a jupyter notebook
If you make a new notebook, select the `{{ cookiecutter.repo_name }}` environment from within the notebook. If you are somehow in another kernel, select **Kernel -> Change kernel -> Python[conda env:{{ cookiecutter.repo_name }}]**. If you don't seem to have that option, make sure that you ran `jupyter notebooks` with the `{{ cookiecutter.repo_name }}` conda environment enabled, and that `which jupyter` points to the correct (`{{ cookiecutter.repo_name }}`) version of jupyter.

If you want your environment changes (or `{{ cookiecutter.module_name }}` module edits) to be immediately available in your running notebooks, make sure to run a notebook cell containing
```
%load_ext autoreload
%autoreload 2
```

More on notebooks can be found in [Using Notebooks for Analysis](notebooks.md).

### Nuke it from orbit
Sometimes, you need to be sure. Making things reproducible means that blowing things away completely and rebuilding from scratch is always an option. To do so:
```
conda deactivate
make delete_environment
make create_environment
conda activate {{ cookiecutter.repo_name }}
touch environment.yml
make update_envrionment
```
and then proceed with managing your environment as above.

### Quick References

* [README](../README.md)
* [Setting up and Maintaining your Conda Environment Reproducibly](conda-environments.md)
* [Getting and Using Datasets](datasets.md)
* [Using Notebooks for Analysis](notebooks.md)
* [Sharing your Work](sharing-your-work.md)
* [Troubleshooting Guide](troubleshooting.md)
