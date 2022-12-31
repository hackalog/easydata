# Getting and Using Datasets

## TL;DR
To get started, all you really need to know is that you can query for available datasets via
```python
from {{ cookiecutter.module_name }}.data import Catalog
Catalog.load("datasets")
```

and load these datasets via
```python
from {{ cookiecutter.module_name }}.data import Dataset
ds = Dataset.load(dataset_name)
```

If you've followed the instructions from building the repo contained in the [README](../README.md), this should just work (if it doesn't, please let us know)!

You can start using the data via `ds.data`. To find out more about the dataset you've just loaded, take a look at `ds.README` and `ds.LICENSE`.

**Disk Space Note**: sometimes datasets can be quite large. If you want to store your data externally, we recommend pointing your data directory to a new location; that is,

```python
from {{ cookiecutter.module_name }} import paths
paths["data_path"] = "/path/to/big/data/directory"
```

## Digging Deeper
It is useful to know a little bit more about how Datasets work.

## What is a `Dataset` object?

A Dataset is the fundamental object we use for turning raw data into useful datasets, reproducibly. It is like a scikit-learn-style `Bunch` object --- essentially, a dictionary with some extra magic to make it nicer to work with --- containing the following attributes:

```
        data: the processed data
        target: (optional) target vector (for supervised learning problems)
        metadata: Data about the data
```

The `data` attribute can really be any processed data form that you like: sometimes it's a pandas dataframe (like with `wine_reviews_130k`), a list of tuples containing other data, (`reddit_comment_tree_graphs`), or other formats including  `scipy.sparse` matrices or `igraph` graphs. The `target` (if you're using it), expects something that matches the `data` in terms of length.

For a hint as to which data format to expect, you can look at the contents of the `README` attribute, one of the many pieces of medata that are maintained as part of the `Dataset` object.

This `metadata` is where things get interesting... which we'll cover on its own next.

## Why `metadata`?
The `metadata` is where the magic lives. It serves several purposes in terms of bookkeeping:

* it includes `HASHES`, which **improve data reproducibility**, since what you download and process gets checked each step along the way to ensure the raw data matches what is stored in the `dataset_catalog`,
* it provides easy access to **what the data is** via the `README` attribute,
* it provides easy (and continual) **access to the license / usage restrictions** for the data (the `LICENSE` attribute), which helps with knowing what you can do when [Sharing your Work](sharing-your-work.md).
* it provides the **fileset data manifest**, `FILESET`, if your dataset includes around additional raw data (extra) files.

In short, it helps you to know what data you're working with, what you can do with it, and whether something has gone wrong.

Under the hood, metadata is a dictionary; however metadata can also be accessed by referring to attributes expressed in uppercase. For example, `ds.metadata['license']` and `ds.LICENSE` refer to the same thing.

## Using a `Dataset`
As mentioned before, to load a `Dataset`:
```python
from {{ cookiecutter.module_name }}.data import Dataset
ds = Dataset.load("<dataset-name>")
```
At this point, if you already have a cached copy of the desired `Dataset` on disk, it will load it. Otherwise, the it will follow the *recipe* for generating the requested `Dataset`; i.e. generate the dataset from raw data, as per the instructions contained in the `dataset_catalog` (described below).

Because of licenses and other distribution restrictions, some of the datasets may require a **manual download** step. If so, you will be prompted at this point and given instructions for what to do. Some datasets will require local pre-processing. If so, the first time your run the command, you will be executing all of the processing scripts (which can be quite slow).

After the first load, however, datasets will load from cache on disk which should be fast. If you need to free up space, you can even delete related source files from `data/raw` and `data/interim`. Just don't touch the `data/processed` directory.

To access the data, target or metdata:
```python
ds.data
ds.target
ds.metadata
```

To access the most common metadata fields:
```python
ds.README          # or ds.metadata['descr']
ds.LICENSE        # or ds.metadata['license']
ds.HASHES         # or ds.metadata['hashes']
```
## The catalog
You can explore all of the currently available `Datasets` via the Dataset `Catalog`. The catalog keeps a record of the recipes used to generate a `Dataset` along with relevant hashes that are used to ensure the integrity of data when it's loaded.

To access the catalog:

```python
from {{ cookiecutter.module_name }}.data import Catalog
Catalog.load("datasets')
```

## Sharing your Data as a `Dataset` object
In order to convert your data to a `Dataset` object, you will need to generate a catalog *recipe*, that uses a custom *function for processing your raw data*. Doing so allows us to document all the munging, pre-processing, and data verification necessary to reproducibly build the dataset.

## What do you mean, LICENSE?
No conversation on sharing data would be complete without a short discussion about data licenses. This will be covered in [Sharing your Work](sharing-your-work.md).


### Quick References

* [README](../README.md)
* [Setting up and Maintaining your Conda Environment Reproducibly](conda-environments.md)
* [Getting and Using Datasets](datasets.md)
* [Using Notebooks for Analysis](notebooks.md)
* [Sharing your Work](sharing-your-work.md)
* [Troubleshooting Guide](troubleshooting.md)
