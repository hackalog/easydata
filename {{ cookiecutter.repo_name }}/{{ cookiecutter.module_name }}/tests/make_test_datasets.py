from sklearn.datasets import fetch_20newsgroups
from functools import partial

from {{ cookiecutter.module_name }}.data import DataSource, Dataset, TransformerGraph
from {{ cookiecutter.module_name }} import workflow, paths
from {{ cookiecutter.module_name }}.log import logger
import {{ cookiecutter.module_name }}.log.debug

# Set up a 20 newsgroups dataset

ds_name = '20_newsgroups'
output_ds_name = ds_name
dsrc = DataSource(ds_name)

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

dsrc.add_metadata(contents=metadata, force=True)
dsrc.add_metadata(contents=license, kind='LICENSE', force=True)

def process_20_newsgroups(*, extract_dir='20_newsgroups',
                          metadata=None, unpack_dir=None,
                          opts={"subset":"all", "remove":"('headers', 'footers', 'quotes')"}):
    """
    Process 20 newsgroups into (data, target, metadata) format.


    Parameters
    ----------
    unpack_dir: path
        The interim parent directory the dataset files have been unpacked into.
    extract_dir: str
        Name of the directory of the unpacked files relative to the unpack_dir. Note that
    opts: dict default {"subset":"all", "remove"="('headers', 'footers', 'quotes')"}
        Options to pass to sklearn.datasets.fetch_20newsgroups.


    Returns
    -------
    A tuple:
        (data, target, additional_metadata)

    """
    if metadata is None:
        metadata = {}

    if unpack_dir is None:
        unpack_dir = paths['interim_data_path']
    else:
        unpack_dir = pathlib.Path(unpack_dir)
    data_dir = unpack_dir / f"{extract_dir}"

    news = fetch_20newsgroups(**opts)

    return news.data, news.target, metadata

process_function = process_20_newsgroups
process_kwargs = {}

dsrc.process_function = partial(process_function, **process_kwargs)
workflow.add_datasource(dsrc)

dag = TransformerGraph(catalog_path=paths['catalog_path'])
dag.add_source(output_dataset=output_ds_name, datasource_name=ds_name, force=True)
