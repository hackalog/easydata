# Using Notebooks for Analysis

Jupyter Notebooks are a fantastic way for doing your EDA and sharing stories about your analysis afterwards. Unfortunately, (and yes, after many years of trying to use notebooks reproducibly, we are opinionated on this) they're a pretty terrible way to share code itself. While we still *love* using notebooks for sharing what we've done with others, especially in a workshop setting.

We've set up this repo in a way to make it easier to use notebooks to share stories, while keeping your code in a python module where it belongs.

Here's our best practices for using notebooks, while keeping your analyses sharable and reproducible. We've also included some of our favourite tricks and tips below for making using notebooks easier. (If you have more, please share them!)

## Naming Convention
Notebooks go in the `notebooks` directory, and are named `dd-xyz-title.ipynb` where:

* `dd` is an integer indicating the notebook sequence. This is critical when there are dependencies between notebooks
* `xyz` is the author's initials, to help avoid namespace clashes when multiple parties are committing to the same repo
* `title` is the name of the notebook, words separated by hyphens.

e.g.`00-xyz-sample-notebook.ipynb`

## Source Control for Notebooks
Here's where the code part of notebooks starts to get tricky. Notebooks awful for using with `git` and other source control systems because of the way that they are stored (giant JSON blob). If you're going to share your notebook back to the main surge repo (which we strongly encourage!):

1. Make sure your cells run sequentially (make sure you can **Kernel->Restart & Run All** successfully)
1. Clear all cell output before checking in your notebook (**Kernel->Restart & Clear Output** before saving).

We realize that clearing the notebook (which gives cleaner diffs and PRs) is a bit of a trade-off against repoducibility of the notebook in that you lose the ability to check cell-by-cell whether you're getting the same results. One way to get around this in your own fork, is to use the `git nbdiff` feature, which is part of the `nbdiff` package (that is installed in this repo by default). You can find it on the right-hand side of the notebook toolbar, asc shown below:

![screenshot](images/toolbar-screenshot.png)

This button will diff the notebook you have open intelligently against the the base version. We like to use `git nbdiff` as a visual diffing tool even if we are clearing output before checking in notebooks.

If you want to give your future users help to see whether they are getting images and figures that match previous analyses, we recommend saving the figures in `reports/figures` and then putting them into a markdown cell in the notebook (so a user can see if what they generated is comparable).

You can also optionally check your notebook in after a successful **Kernel->Restart & Run All**. This is a little more work to maintain diffs on, but can be nicer for communication withouit having to run a notebook to see what the results look like.

## On code
As mentioned, notebooks aren't a great place for keeping code, as diffs and PRs in a notebook are virtually unreadable. This repo uses an editable python module called `{{ cookiecutter.module_name }}`. If you write code that you'd like to use in a notebook (e.g. `my_python_file.py`), put it in the `{{ cookiecutter.module_name }}/xyz` directory where `xyz` is the author's initials. You should then be able to immediately load it in your notebook via:
```python
from {{ cookiecutter.module_name }}.xyz.my_python_file import my_function_name
```
If it's not immediately loading (or you need to restart your kernel to make it visible), make sure you run the following cell (preferably at the top of your notebook...see more on useful header cells below):
```python
%load_ext autoreload
%autoreload 2
```

## Jupyter Tips and Tricks
First up, if you're in a notebook, keyboard shortcuts can be found using the `Esc` key. Use them.

### Useful Header Cells
#### Better display
This cell makes your jupyter notebook use the full screen width. Put this as your first executable cell. You'll thank us.
```python
from IPython.core.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))
```
#### Autoreloading
The cell
```python
%load_ext autoreload
%autoreload 2
```
let's you autoreload code that's changed in your environment. This means you can update your environment without killing your kernel or develop code in the `{{ cookiecutter.module_name }}` module that is immediately available via auto-reload.
#### Python Libraries
It helps to put your dependencies at the top of your notebook. Ours usually look something like this:
```python
# Python Imports, alphabetized
import pathlib
...

#3rd party python modules, alphabetized
import pandas as pd
...

#Some plotting libraries
import matplotlib.pyplot as plt
%matplotlib notebook
from bokeh.plotting import show, save, output_notebook, output_file
from bokeh.resources import INLINE
output_notebook(resources=INLINE)

# Source module imports
from {{ cookiecutter.module_name }} import paths
from {{ cookiecutter.module_name }}.data import DataSource, Dataset, Catalog
```
You can also find most of these header cells in [00-xyz-sample-notebook.ipynb](../notebooks/00-xyz-sample-notebook.ipynb)

### Cell Magics
There is a whole world of cell magics. These are bits of code that you can put at the top of a cell that do magical things. A few of our most used ones are:

* `%%time`: time the cell (use this on slow cells)
* `%debug`: invoke the python debugger (make sure to `exit` when you're done)
* `%%file`: write current cell's content to a file (use `-a` to append)
* `%load`: load a file's contents into the current cell
* `%%bash`: run the cell using bash kernel


### Quick References

* [README](../README.md)
* [Setting up and Maintaining your Conda Environment, Reproducibly](conda-environments.md)
* [Getting and Using Datasets](datasets.md)
* [Specifying Paths in Easydata](paths.md)
* [Using Notebooks for Analysis](notebooks.md)
* [Sharing your Work](sharing-your-work.md)
* [Troubleshooting Guide](troubleshooting.md)
