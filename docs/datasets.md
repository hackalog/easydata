# Datasets

Easydata lets you build a dataset catalog from which you can load any dataset in the catalog via its `dataset_name` via the `.load` API.
```python
ds = Dataset.load(dataset_name)
```
The basic idea is that we don't want to share data directly, instead, we share the recipes for how to re-create Datasets. These recipes are stored in the dataset catalog. Datasets can then be shared by sharing the catalog.

Datasets are the fundamental object that makes sharing of datasets reproducible, as they keep track of their own recipes, check that the data created from a recipe has the correct hashes, and keep licenses and other metadata with the data itself.

## What is a `Dataset` object?

A Dataset is the fundamental object we use for turning raw data into useful datasets, reproducibly. It is like a scikit-learn-style `Bunch` object---essentially, a dictionary with some extra magic to make it nicer to work with---containing the following attributes:

```bash
        data: the processed data
        target: (optional) target vector (for supervised learning problems)
        metadata: Data about the data
```

The `data` attribute can really be any processed data form that you like: sometimes it's a pandas dataframe, a list of tuples containing other data, or other formats including  `scipy.sparse` matrices or `igraph` graphs. The `target` (if you're using it), expects something that matches the `data` in terms of length.

For a hint as to which data format to expect, you can look at the contents of the `DESCR` attribute, one of the many pieces of medata that are maintained as part of the `Dataset` object.

This `metadata` is where things get interesting... which we'll cover on its own next.

## Why `metadata`?
The `metadata` is where the magic lives. It serves several purposes in terms of bookkeeping:

* it includes `HASHES`, which **improve data reproducibility**, since what you download and process gets checked each step along the way to ensure the raw data matches what is stored in the `dataset_catalog`,
* it provides easy access to **what the data is** via the `DESCR` attribute,
* it provides easy (and continual) **access to the license / usage restrictions** for the data (the `LICENSE` attribute), which helps with knowing what you can do when [Sharing your Work](sharing-your-work.md).
* it provides the **extra data manifest**, `EXTRA`, if your dataset includes around additional raw data (extra) files.

In short, it helps you to know what data you're working with, what you can do with it, and whether something has gone wrong.

Under the hood, metadata is a dictionary; however metadata can also be accessed by referring to attributes expressed in uppercase. For example, `ds.metadata['license']` and `ds.LICENSE` refer to the same thing.

## Using a `Dataset`
As mentioned before, to load a `Dataset`:
```python
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
ds.DESCR          # or ds.metadata['descr']
ds.LICENSE        # or ds.metadata['license']
ds.HASHES         # or ds.metadata['hashes']
```
## The Dataset catalog
You can explore all of the currently available `Datasets` via the dataset catalog. The catalog keeps a record of the recipes used to generate a `Dataset` along with relevant hashes that are used to ensure the integrity of data when it's loaded.

To access the catalog:

```python
workflow.available_datasets(keys_only=True)
```
If you're interested, set `keys_only=False` to see the complete contents of the metadata that is saved in the catalog.

## Creating Dataset Recipes

For the curious...

The API for adding datasets is not yet user friendly, but we are currently working on making it so.

When to create a dataset:

* If you're even tempted to save some data to disk so you don't have to recompute it later,
* If you're even tempted to save data to share with someone else,
* If you want to access your data from another notebook/code path,
* If you feel like it :)

We have included some examples to let you look under the hood if you're interested, and have included some common examples as part of the `workflow` module to make it easier to use.

Example notebooks using the built-in `workflow`:

* [Creating a dataset from a csv file](../Add-csv-template)
* [Creating a derived dataset using a single function](../Add-derived-dataset)

Example notebooks for generally building datasets:

* [Dataset from raw file](../New-Dataset-Template)
* [Dataset from another dataset](../New-Edge-Template)

You can also make datasets from multiple existing datasets, or make multiple datasets at once.

Some datasets are trickier to include than others and may used advanced functionality. So please ask any questions that you may have. We'll attempt to explain and update the examples based on requests.