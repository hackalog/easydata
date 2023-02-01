from sklearn.datasets import fetch_20newsgroups
from functools import partial

from {{ cookiecutter.module_name }}.data import DataSource, Dataset, DatasetGraph, Catalog
from {{ cookiecutter.module_name }}.data.process_functions import process_20_newsgroups
from {{ cookiecutter.module_name }} import paths
from {{ cookiecutter.module_name }}.log import logger

# Set up a 20 newsgroups dataset

license = """
Custom Academic License: "You may use this material free of charge for any educational purpose, provided attribution is given in any lectures or publications that make use of this material." As in http://kdd.ics.uci.edu/databases/20newsgroups/20newsgroups.data.html.
"""
metadata = """
The 20 Newsgroups dataset is a collection of approximately 20,000 newsgroup documents, partitioned (nearly) evenly across 20 different newsgroups.

The data is organized into 20 different newsgroups, each corresponding to a different topic. Some of the newsgroups are very closely related to each other (e.g. comp.sys.ibm.pc.hardware / comp.sys.mac.hardware), while others are highly unrelated (e.g misc.forsale / soc.religion.christian).

Here are the categories:

 * `alt.atheism`,
 * `comp.graphics`,
 * `comp.os.ms-windows.misc`,
 * `comp.sys.ibm.pc.hardware`,
 * `comp.sys.mac.hardware`,
 * `comp.windows.x`,
 * `misc.forsale`,
 * `rec.autos`,
 * `rec.motorcycles`,
 * `rec.sport.baseball`,
 * `rec.sport.hockey`,
 * `sci.crypt`,
 * `sci.electronics`,
 * `sci.med`,
 * `sci.space`,
 * `soc.religion.christian`,
 * `talk.politics.guns`,
 * `talk.politics.mideast`,
 * `talk.politics.misc`,
 * `talk.religion.misc`

The current version is obtained by wrapping `sklearn.datasets.fetch_20newsgroups`, which comes from this [20 newsgroups webpage](http://qwone.com/~jason/20Newsgroups/).

By default we follow the sklearn suggestion to set `remove=('headers', 'footers', 'quotes')` to avoid overfitting.
"""
if __name__ =='__main__':
    ds_name = '20_newsgroups'
    output_ds_name = ds_name
    dsrc = DataSource(ds_name)

    dsrc.add_metadata(contents=metadata, force=True)
    dsrc.add_metadata(contents=license, kind='LICENSE', force=True)

    process_function = process_20_newsgroups
    process_kwargs = {}

    dsrc.process_function = partial(process_function, **process_kwargs)
    dsrc.update_catalog()

    dag = DatasetGraph()
    dag.add_source(output_dataset=output_ds_name, datasource_name=ds_name, overwrite_catalog=True)
