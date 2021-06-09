import pathlib

import pandas as pd
from tqdm.auto import tqdm

from sklearn.model_selection import train_test_split

from . import Dataset, deserialize_partial
from .. import paths
from ..log import logger
from .utils import deserialize_partial
from ..utils import run_notebook

__all__ = [
    'run_notebook_transformer',
    'apply_single_function',
    'csv_to_pandas',
    'new_dataset',
    'sklearn_train_test_split',
    'sklearn_transform',
]

def run_notebook_transformer(dsdict, *,
                             notebook_name,
                             notebook_path,
                             output_dataset_names,
                             ):
    """
    Use a notebook as a transformer function in the dataset graph.
    The notebook *must* write the output datasets to disk; i.e. once their
    notebook has run, this function assumes Dataset.from_disk() will succeed
    for all output datasets listed in `output_dataset_names`

    Parameters
    ----------
    dsdict: Ignored
        Needed to conform to transformer API, but ignored, as these will need
        to be loaded in the notebook itself.
    notebook_name: None or str
        Name of current notebook. If None, an attempt will be made to infer it.
    notebook_path: None or str or Path
        If None, paths['notebook_path'] will be used
    output_dataset_names: List(str)
        List of datasets that were created (and saved to disk) by the notebook.
        These will be loaded from disk and returned by the transformer
    """
    if notebook_path == 'None':
        logger.error("JSON encoding problem with notebook_path. Please regenerate transformer")

    logger.debug(f"Using notebook:{notebook_name} as transformer to generate {output_dataset_names}")
    output_notebook = run_notebook(notebook_path=notebook_path, notebook_name=notebook_name)
    logger.debug(f"See {paths['interim_data_path']/output_notebook} for output of this process")
    ods_dict = {}
    for ods in output_dataset_names:
        logger.debug(f"Loading output dataset:{ods} from disk")
        ods_dict[ods] = Dataset.from_disk(ods)
    return ods_dict


def new_dataset(dsdict, *, dataset_name, dataset_opts=None):
    """
    Transformer function: create a dataset from its default constructor

    Parameters
    ----------
    dsdict: ignored

    dataset_name:
        Name of dataset to create
    dataset_opts: dict
        kwargs dict to pass to Dataset constructor

    Returns
    -------
    dsdict {dataset_name: Dataset}
    """
    if dataset_opts is None:
        dataset_opts = {}
    ds = Dataset(dataset_name, **dataset_opts)
    return {dataset_name: ds}

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

def csv_to_pandas(ds_dict, *, output_map, **opts):
    """

    Parameters
    ----------
    ds_dict:
        input datasets. If multiple datasets, processing will stop at first matching csv_filename
    output_map: dict(new_dataset_name:csv_filename)
        datasets to create. new_dataset_name will be created using csv_filename as its data column.
    **opts:
        Remaining options will be ignored
    """
    new_ds = {}
    df = None
    for ds_name, dset in ds_dict.items():
        extra = dset.metadata.get('extra', None)
        if extra is not None:
            logger.debug(f"Input dataset {ds_name} has extra data. Processing...")
            for rel_dir, file_dict in extra.items():
                for new_dsname, csv_filename in output_map.items():
                    if csv_filename in file_dict:
                        logger.debug(f"Found {csv_filename}. Creating {new_dsname} dataset")
                        path = paths['processed_data_path'] / rel_dir / csv_filename
                        df = pd.read_csv(path)
                        new_metadata = dset.metadata
                        new_metadata.pop('extra', None)
                        new_ds[new_dsname] = Dataset(dataset_name=new_dsname, data=df, metadata=new_metadata)
    return new_ds



def apply_single_function(ds_dict, *, source_dataset_name, dataset_name, serialized_function, added_descr_txt, drop_extra, **opts):
    """
    Parameters
    ----------
    ds_dict:
        input datasets.
    source_dataset_name:
        name of the dataset that the new dataset will be derived from
    dataset_name:
        name of the new dataset_catalog
    added_descr_txt: Default None
        new description text to be appended to the metadata descr
    serialized_function:
        function (serialized by src.utils.serialize_partial) to run on .data to produce the new .data
    drop_extra: boolean
        drop the .extra part of the metadata
    **opts:
        Remaining options will be ignored
    """

    new_ds = {}

    logger.debug(f"Loading {source_dataset_name}...")
    ds = ds_dict.get(source_dataset_name)

    new_metadata = ds.metadata.copy()
    new_metadata['descr'] += added_descr_txt
    if drop_extra:
        if new_metadata.get('extra', 0) != 0:
            new_metadata.pop('extra')

    logger.debug(f"Applying data function...")
    data_function=deserialize_partial(serialized_function)
    new_data = data_function(ds.data)

    if ds.target is not None:
        new_target = ds.target.copy()
    else:
        new_target = None

    new_ds[dataset_name] = Dataset(dataset_name=dataset_name, data=new_data, target=new_target, metadata=new_metadata)
    return new_ds


    new_metadata = ds.metadata.copy()

    new_ds[new_dsname] = Dataset(dataset_name=new_dsname, data=preprocessed_corpus, metadata=new_metadata)
    return new_ds

def limit_to_common_varietals(df, min_reviews=25):
    '''
    Take the subselection of the wine reviews dataset (df) that only contains varietals with at least
    min_reviews reviews. All entries in the final dataframe must have a variety.

    Parameters
    ----------
    df: DataFrame
        wine reviews dataframe with 'variety' as  a column
    min_reviews: int
        minimum number of reviews needed to keep a varietal

    Returns
    -------
    df_common_variety:
        dataframe that only includes reviews with a variety that appears at least min_reviews times.
    '''
    df_variety = df.dropna(axis=0, subset=['variety']).copy()

    varietal_counts = df_variety.variety.value_counts()
    df_variety['common_varietal'] = df_variety.variety.apply(lambda x: varietal_counts[x] > min_reviews)

    df_common_variety = df_variety[df_variety.common_varietal].copy()
    df_common_variety.reset_index(inplace=True)
    df_common_variety.drop(columns=['index', 'common_varietal'], inplace=True)

    return df_common_variety
