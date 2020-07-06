import pathlib

from sklearn.datasets import fetch_20newsgroups
from sklearn.model_selection import train_test_split

from . import Dataset

__all__ = [
    'sklearn_20newsgroups',
    'sklearn_train_test_split',
    'sklearn_transform',
]

def sklearn_20newsgroups(
    ds_dict=None,
    data_home=None,
    subset='all',
    categories=None,
    shuffle=True,
    random_state=42,
    remove=(),
):
    """Dataset Transformer: Import the 20newsgroups Dataset from sklearn.

    Parameters
    ----------
    data_home : optional, default: None
        Specify a download and cache folder for the datasets. If None,
        all scikit-learn data is stored in '~/scikit_learn_data' subfolders.

    subset : 'train' or 'test', 'all', optional
        Select the dataset to load: 'train' for the training set, 'test'
        for the test set, 'all' for both, with shuffled ordering.

    categories : None or collection of string or unicode
        If None (default), load all the categories.
        If not None, list of category names to load (other categories
        ignored).

    shuffle : bool, optional
        Whether or not to shuffle the data: might be important for models that
        make the assumption that the samples are independent and identically
        distributed (i.i.d.), such as stochastic gradient descent.

    random_state : int, RandomState instance or None (default)
        Determines random number generation for dataset shuffling. Pass an int
        for reproducible output across multiple function calls.
        See :term:`Glossary <random_state>`.

    remove : tuple
        May contain any subset of ('headers', 'footers', 'quotes'). Each of
        these are kinds of text that will be detected and removed from the
        newsgroup posts, preventing classifiers from overfitting on
        metadata.

        'headers' removes newsgroup headers, 'footers' removes blocks at the
        ends of posts that look like signatures, and 'quotes' removes lines
        that appear to be quoting another post.

        'headers' follows an exact standard; the other filters are not always
        correct.


    Returns
    -------
    dict {dataset_name : dataset}

    where `dataset` is a Dataset object with the following attribute:

    * data: list, length [n_samples]
    * target: array, shape [n_samples]
    * metadata, including:
        * n_samples
        * filenames: list, length [n_samples]
        * DESCR: a description of the dataset.
        * LICENSE: the license for the dataset
        * target_names: a list of categories of the returned data,
          length [n_classes]. This depends on the `categories` parameter.

    """
    if data_home is None:
        data_home = paths['raw_data_path']
    else:
        data_home = pathlib.Path(data_home)

    dataset = fetch_20newsgroups(data_home=data_home,
                                 subset=subset,
                                 categories=categories,
                                 shuffle=shuffle,
                                 random_state=random_state,
                                 remove=remove,
                                 return_X_y=False,
                                 download_if_missing=True)
    dset = Dataset(dataset_name=f"20news-{subset}")
    dset.data = dataset.data
    dset.target = dataset.target
    dset.FILENAMES = dataset.filenames
    dset.N_SAMPLES = len(dataset.filenames)
    dset.TARGET_NAMES = dataset.target_names

    readme_txt = f"""# The 20news-{subset} Data Set
    ## Overview

    The [20 Newsgroups] data set is a collection of approximately 20,000
    newsgroup documents, partitioned (nearly) evenly across 20 different
    newsgroups. To the best of my knowledge, it was originally collected
    by Ken Lang, probably for his [Newsweeder]: Learning to filter netnews
    paper, though he does not explicitly mention this collection. The 20
    newsgroups collection has become a popular data set for experiments
    in text applications of machine learning techniques, such as text
    classification and text clustering.

    [newsweeder]: http://qwone.com/~jason/20Newsgroups/lang95.bib
    [20 newsgroups]: http://people.csail.mit.edu/jrennie/20Newsgroups/

    ## Organization

    The data is organized into 20 different newsgroups, each
    corresponding to a different topic. Some of the newsgroups are
    very closely related to each other (e.g. comp.sys.ibm.pc.hardware
    / comp.sys.mac.hardware), while others are highly unrelated (e.g
    misc.forsale / soc.religion.christian). Here is a list of the 20
    newsgroups, partitioned (more or less) according to subject
    matter:

    * comp.graphics
    * comp.os.ms-windows.misc
    * comp.sys.ibm.pc.hardware
    * comp.sys.mac.hardware
    * comp.windows.x
    * rec.autos
    * rec.motorcycles
    * rec.sport.baseball
    * rec.sport.hockey
    * sci.crypt
    * sci.electronics
    * sci.med
    * sci.space
    * misc.forsale
    * talk.politics.misc
    * talk.politics.guns
    * talk.politics.mideast
    * talk.religion.misc
    * alt.atheism
    * soc.religion.christian

    ## Data

    The data available here are in .tar.gz bundles. You will need tar and
    gunzip to open them. Each subdirectory in the bundle represents a
    newsgroup; each file in a subdirectory is the text of some newsgroup
    document that was posted to that newsgroup.

    Below are three versions of the data set. The first ("19997") is the
    original, unmodified version. The second ("bydate") is sorted by date
    into training(60%) and test(40%) sets, does not include cross-posts
    (duplicates) and does not include newsgroup-identifying headers (Xref,
    Newsgroups, Path, Followup-To, Date). The third ("18828") does not
    include cross-posts and includes only the "From" and "Subject"
    headers.

    * [19997] - Original 20 Newsgroups data set
    * [bydate] - 20 Newsgroups sorted by date; duplicates and
      some headers removed (18846 documents)
    * [18828] - 20 Newsgroups; duplicates removed, only "From"
      and "Subject" headers (18828 documents)

    [19997]: http://qwone.com/~jason/20Newsgroups/20news-19997.tar.gz
    [bydate]: http://qwone.com/~jason/20Newsgroups/20news-bydate.tar.gz
    [18828]: http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz

    The"bydate" version is recommended, since cross-experiment comparison is
    easier (no randomness in train/test set selection),
    newsgroup-identifying information has been removed and it's more
    realistic because the train and test sets are separated in time.
    """
    license_txt = """This text was believed to be collected by Ken Lang,
    probably for his [Newsweeder]: Learning to filter netnews paper.

    [newsweeder]: http://qwone.com/~jason/20Newsgroups/lang95.bib

    It is presumed to be in the public domain.
    """
    dset.LICENSE = license_txt
    dset.DESCR = readme_txt
    return {dset.name:dset}


def sklearn_train_test_split(ds_dict, **split_opts):
    """Transformer Function: performs a train/test split.

    for each `dset` in ds_dict, this transformer creates two new
    datasets: {dset.name}_test and {dset.name}_train

    Parameters
    ----------
    ds_dict:
        input datasets
    **split_opts:
        Remaining options will be passed to `train_test_split`

    """
    new_ds = {}
    for ds_name, dset in ds_dict.items():

        for kind in ['train', 'test']:
            dset_name = f"{dset_name}_{kind}"
            dset_meta = {**dset.metadata, 'split':kind, 'split_opts':split_opts}
            new_ds[dset_name] = Dataset(dataset_name=dset_name, metadata=dset_meta)
        X_train, X_test, y_train, y_test = train_test_split(dset.data, dset.target, **split_opts)

        new_ds[f'{dset_name}_train'].data = X_train
        new_ds[f'{dset_name}_train'].target = y_train
        new_ds[f'{dset_name}_test'].data = X_test
        new_ds[f'{dset_name}_test'].target = y_test
    return new_ds

def sklearn_transform(ds_dict, transformer_name, transformer_opts=None, subselect_column=None, **opts):
    """
    Wrapper for any 1:1 (data in to data out) sklearn style transformer. Will run the .fit_transform
    method of the transformer on dset.data. If subselect_column is not None, it will treat the data
    like a dataframe and will subselect dset.data[subselect_column] to run the transformer on.

    Parameters
    ----------
    ds_dictet:
        Datasets upon which to apply transforms
    transformer_name: string
        sklearn style transformer with a .fit_transform method avaible via sklearn_transformers.
    transformer_opts: dict
        options to pass on to the transformer
    subselect_column: string
        column name for dset.data to run the transformer on
    return_whole: boolean
        return the whole dataframe with a new column named "transformed"
    **opts:
        options to pass on to the fit_transform method

    Returns
    -------
    Datasets whose data are the result of the transformer.fit_transform
    """
    new_dsdict = {}
    for ds_name, dset in ds_dict.items():
        if transformer_name in sklearn_transformers():
            transformer = sklearn_transformers(keys_only=False).get(transformer_name)(**transformer_opts)
        else:
            raise ValueError(f"Invalid transformer name: {transformer_name}. See sklearn_transformers for available names.")
        if subselect_column:
            new_data = transformer.fit_transform(dset.data[subselect_column], **opts)
        else:
            new_data = transformer.fit_transform(dset.data, **opts)

        new_dsname = f"{dset.name}_{transformer.__class__.__name__}"
        new_dsdict[new_dsname] = Dataset(dataset_name=new_dsname, metadata=dset.metadata, data=new_data)
    return new_dsdict
