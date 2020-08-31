## Troubleshooting Guide

It's impossible to test the configurations on every possible machine, so we haven't caught everything. But we're working on making fixes as problems come up. Here's what we've encountered so far (with links to the issues in question if you want to deep dive into the fix).

Before you report a problem, make sure you are running the latest version of the surge repo.
Assuming you are following the [recommended git workflow](https://github.com/hackalog/cookiecutter-easydata/wiki/Github-Workflow-Cheat-Sheet) (i.e. you have set your `upstream` remote to point to the surge repo, you are working in a branch, and your `master` branch is tracking the surge repo), this means doing a:
```
git checkout master
git fetch upstream --prune
git merge upstream/master
git push origin master
make update_environment
```

You can then update your working branches as follows:
```
git checkout my_branch
git merge master  # advanced git users can do a rebase here. Others please merge.
```

Next, turn on debugging in your notebook. Add these cells to the top:
```
import logging
from {{ cookiecutter.module_name }}.log import logger

logger.setLevel(logging.DEBUG)
```

Third, ensure your notebook is running the correct environment; i.e. select **Kernel -> Change kernel -> Python[conda env:{{ cookiecutter.repo_name }}]**. If you don't seem to have that option, make sure that you ran `jupyter notebooks` with the `{{ cookiecutter.repo_name }}` conda environment enabled, and that `which jupyter` points to the correct ({{ cookiecutter.repo_name }}) version of jupyter.


If your problem persists, work through the table below. If these fail to resolve your issue, please post your issue. Include with your issue:

* A copy/pasted copy of the error traceback text (preferably posted as a "code snippet"), including DEBUG-level log messages.
* The contents of your `environment.*.lock.yml`
* the output of `%conda info` (run from within your jupyter notebook)
* The output of `which python` and `which jupyter`

| Problem  | Status                    | Fix  |
| :---          |    :----                             |   :----                             |
| General weirdness due to not being in the right conda environment  | **Try this first**  | `conda activate {{ cookiecutter.repo_name }}` or change the kernel in your jupyter notebook |
| Old conda (e.g. `{{ cookiecutter.module_name }}` module is not being installed correctly) | **Try this second**| Upgrade conda to version > 4.8 |
| `{{ cookiecutter.module_name }}` module not found | **Try this first** | `conda activate {{ cookiecutter.repo_name }}`|
| `{{ cookiecutter.module_name }}` module still doesn't work | **Try this second** | `touch environment.yml && make update_environment` |
| Nothing works | Take off and nuke it from orbit | `conda deactivate && make delete_environment && make create_environment`|

### Other specific troubleshooting FAQ

If `import cairo` fails, this may suggest some library (such as `libXrender.so`) could be missing. If you’ve followed all the troubleshooting instructions above, then proceed.

There is an open issue with Conda's handling of system dependencies related to the Cairo library, which is used for graph visualization through the `igraph` library, amongst other things. Seemingly, on cloud-borne virtual machines, such libraries that are common on desktop installs go undeployed, a fact that Conda apparently neglects.

Once can work around this issue by locally installing the missing dependency through their system's package manager (e.g. APT, Yum, Homebrew, and so on). For instance, on Ubuntu 18.04, the aforementioned Xrender library can be installed with the command

```
sudo apt-get install -y libxrender-dev
```


### Quick References

* [README](../README.md)
* [Setting up and Maintaining your Conda Environment Reproducibly](conda-environments.md)
* [Getting and Using Datasets](datasets.md)
* [Using Notebooks for Analysis](notebooks.md)
* [Sharing your Work](sharing-your-work.md)
