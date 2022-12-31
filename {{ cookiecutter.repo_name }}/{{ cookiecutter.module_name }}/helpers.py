## Script common ways of adding a dataset to the workflow

from functools import partial
import fsspec
import pathlib
import os

from .log import logger
from . import paths
from .exceptions import EasydataError

from .data import (DataSource, Dataset, hash_file, DatasetGraph, Catalog,
               serialize_transformer_pipeline)
from .data.transformer_functions import csv_to_pandas, new_dataset, apply_single_function, run_notebook_transformer
from .data.fileset import process_fileset_files
from .data.utils import serialize_partial

__all__ = [
    'dataset_from_csv_manual_download',
    'dataset_from_fsurl',
    'dataset_from_metadata',
    'dataset_from_single_function',
    'derived_dataset',
    'metadata_from_fsspec',
    'notebook_as_transformer',
]


def notebook_as_transformer(notebook_name, *,
                            input_datasets=None,
                            output_datasets,
                            overwrite_catalog=False,
                            notebook_path=None,
                            transformer_name=None
                            ):
    """Use a Jupyter notebook as a Dataset transformer funtion.

    This helper simplifies the process of using a jupyter notebook as a transformer function
    in the DatasetGraph.

    Parameters
    ----------
    notebook_name: string
        filename of notebook. relative to `notebook_path`. Obviously, notebook must exist

    """

    if notebook_path is not None:
        notebook_fq = pathlib.Path(notebook_path) / notebook_name
        notebook_path = str(notebook_path)
    else:
        notebook_fq = paths['notebook_path'] / notebook_name

    dag = DatasetGraph()
    write_dataset_to_catalog = write_transformer_to_catalog = overwrite_catalog

    if not notebook_fq.exists():
        raise EasydataError(f"Notebook {notebook_fq} does not exist. Cannot be used as transformer.")

    dsdict = {}
    for ods in output_datasets:
        ods.update_hashes()
        if ods.name in dag.datasets:
            logger.debug(f"dataset:{ods.name} already in catalog")

            if dag.check_dataset_hashes(ods.name, ods.HASHES):
                logger.debug(f"Hashes match for {ods.name}. Skipping Overwrite.")
                write_dataset_to_catalog = False
            else:
                logger.warning(f"Hashes do not match for {ods.name}")
                if overwrite_catalog is False:
                    raise ValidationError(f"Hashes for Dataset:{ods.name} differ from catalog, but overwrite_catalog is False")
        else:
            logger.debug(f"dataset:{ods.name} not in catalog. Adding...")
            write_dataset_to_catalog=True

        logger.debug(f"Writing dataset:{ods.name} to disk")
        ods.dump(exists_ok=True, update_catalog=write_dataset_to_catalog)

        logger.debug(f"Generating Transformer edge")
        transformers = [partial(run_notebook_transformer,
                                notebook_path=notebook_path,
                                notebook_name=notebook_name,
                                output_dataset_names=[ds.name for ds in output_datasets])]

        transformer = dag.add_edge(input_datasets=[ds.name for ds in input_datasets],
                                   output_datasets=[ds.name for ds in output_datasets],
                                   transformer_pipeline=serialize_transformer_pipeline(transformers),
                                   overwrite_catalog=write_transformer_to_catalog,
                                   edge_name=transformer_name,
                                   generate=False)

        dsdict[ods.name] = ods
    return dsdict

# Create a Dataset from a single csv file
def dataset_from_csv_manual_download(ds_name, csv_path, download_message,
                                     license_str, readme_str, *, hash_type='sha1',
                                     hash_value=None,
                                     overwrite_catalog=False,):
    """
    Add a dataset to the catalog files where .data is the dataframe from a
    single .csv file obtained via manual download.

    ds_name: str
        name of the resulting dataset
    csv_path: path
        relative path to the .csv file from paths['raw_data_path']
    download_message: str
    hash_type: {'sha1', 'md5'}
    hash_value: string. required
        Hash, computed via the algorithm specified in `hash_type`
    license_str: str
        Contents of metadata license as text
    readme_str:
        Contents of the metadata description as text
    overwrite_catalog: boolean
        If True, existing entries in datasets and transformers catalogs will be
        overwritten

    Returns
    -------
    Dataset that was added to the Transformer graph
    """

    dataset_catalog = Catalog.load('datasets')
    if ds_name in dataset_catalog and not overwrite_catalog:
        raise KeyError(f"'{ds_name}' already in catalog")
    csv_path = pathlib.Path(csv_path)
    # Create a datasource
    raw_ds_name = ds_name+"-raw"
    logger.debug(f"Creating raw datasource: {raw_ds_name}")
    dsrc = DataSource(raw_ds_name)

    if hash_value is None:
        file_path = paths['raw_data_path'] / csv_path
        hash_value = hash_file(file_path, algorithm=hash_type)
    dsrc.add_manual_download(message=download_message,
                             file_name=str(csv_path),
                             hash_type=hash_type,
                             hash_value=hash_value,
                             unpack_action='copy',
                             force=True)
    dsrc.add_metadata(contents=readme_str, force=True)
    dsrc.add_metadata(contents=license_str, kind='LICENSE', force=True)

    process_function = process_fileset_files
    process_function = process_fileset_files
    process_function_kwargs = {'do_copy':True,
                               'file_glob':str(csv_path.name),
                               'fileset_dir': raw_ds_name+'.fileset',
                               'extract_dir': raw_ds_name}
    dsrc.process_function = partial(process_function, **process_function_kwargs)
    datasource_catalog = Catalog.load('datasources')
    datasource_catalog[dsrc.name] = dsrc.to_dict()

    # Add a dataset from the datasource
    dag = DatasetGraph(catalog_path=paths['catalog_path'])
    dag.add_source(output_dataset=raw_ds_name, datasource_name=raw_ds_name, overwrite_catalog=True)
    # Run the dataset creation code to add it to the catalog
    ds = Dataset.from_catalog(raw_ds_name)

    # Add transformer to create the final dataset
    transformers = [partial(csv_to_pandas,
                            output_map={ds_name:csv_path.name})]

    dag.add_edge(input_dataset=raw_ds_name,
                 output_dataset=ds_name,
                 transformer_pipeline=serialize_transformer_pipeline(transformers),
                 overwrite_catalog=True)

    ds = Dataset.from_catalog(ds_name)
    return ds

def dataset_from_metadata(dataset_name, metadata=None, overwrite_catalog=False):
    """Create Dataset from supplied metadata

    Dataset will be a source node in the Transformer graph

    Parameters
    ----------
    dataset_name:
        name of dataset to be created
    metadata:
        dictionary of metadata fields for dataset creation
    overwrite_catalog: boolean
        If True, existing entries in datasets and transformers catalogs will be
        overwritten

    Returns
    -------
    Dataset that was added to the Transformer graph

    """
    dataset_catalog = Catalog.load('datasets')
    if dataset_name in dataset_catalog and not overwrite_catalog:
        raise KeyError(f"'{dataset_name}' already in catalog")
    if metadata is None:
        metadata = {}
    dag = DatasetGraph()
    ds_opts = {'metadata': metadata}
    transformers = [partial(new_dataset, dataset_name=dataset_name, dataset_opts=ds_opts)]
    dag.add_source(output_dataset=dataset_name,
               transformer_pipeline=serialize_transformer_pipeline(transformers),
               overwrite_catalog=overwrite_catalog)
    ds = Dataset.from_catalog(dataset_name)
    return ds


def dataset_from_single_function(*, source_dataset_name, dataset_name, data_function, added_readme_txt, drop_fileset=True, overwrite_catalog=False):
    """
    Create a derived dataset (dataset_name) via a single function call on .data from a
    previous dataset (source_dataset_name).

    Parameters
    ----------
    source_dataset_name:
        name of the dataset that the new dataset will be derived from
    dataset_name:
        name of the new dataset_catalog
    added_readme_txt: Default None
        new description text to be appended to the metadata readme
    data_function:
        function (from src module) to run on .data to produce the new .data
    overwrite_catalog: boolean
        if True, existing entries in datasets and transformers catalogs will be overwritten
    """
    dag = DatasetGraph(catalog_path=paths['catalog_path'])
    serialized_function = serialize_partial(data_function)
    transformers = [partial(apply_single_function, source_dataset_name=source_dataset_name, dataset_name=dataset_name,
                            serialized_function=serialized_function, added_readme_txt=added_readme_txt, drop_fileset=drop_fileset)]
    dag.add_edge(input_dataset=source_dataset_name,
                 output_dataset=dataset_name,
                 transformer_pipeline=serialize_transformer_pipeline(transformers),
                 overwrite_catalog=overwrite_catalog)
    ds = Dataset.from_catalog(dataset_name)
    logger.debug(f"{dataset_name} added to catalog")
    return ds

def derived_dataset(*, dataset_name, source_dataset_name, added_readme_txt,
                    drop_fileset=True, drop_data=True, drop_target=False,
                    overwrite_catalog=False):
    """
    Create a derived dataset (dataset_name) via a single function call on .data from a
    previous dataset (source_dataset_name).

    Parameters
    ----------
    source_dataset_name:
        name of the dataset that the new dataset will be derived from
    dataset_name:
        name of the new dataset_catalog
    added_readme_txt: Default None
        new description text to be appended to the metadata readme
    drop_fileset: boolean
        If True, don't copy fileset data to new dataset
    drop_data: boolean
        If True, don't copy data to new dataset
    drop_target: boolean
        If True, don't copy target to new dataset
    overwrite_catalog: boolean
        if True, existing entries in datasets and transformers catalogs will be overwritten
    """
    dag = DatasetGraph(catalog_path=paths['catalog_path'])
    serialized_function = serialize_partial(data_function)
    transformers = [partial(copy_dataset, source_dataset_name=source_dataset_name, dataset_name=dataset_name,
                            added_readme_txt=added_readme_txt, drop_fileset=drop_fileset, drop_data=drop_data, drop_target=drop_target)]
    dag.add_edge(input_dataset=source_dataset_name,
                 output_dataset=dataset_name,
                 transformer_pipeline=serialize_transformer_pipeline(transformers),
                 overwrite_catalog=overwrite_catalog)
    ds = Dataset.from_catalog(dataset_name)
    logger.debug(f"{dataset_name} added to catalog")
    return ds

def metadata_from_fsspec(fs, path, metadata=None, fileset=None):
    """Create metadata, FILESET file list from fsspec URL.

    Creates a metadata dict representing a dataset

    + filenames in all uppercase are assumed to be metadata fields
    + remaining files are used to populate FILESET data and have their hashes computed.

    Parameters
    ----------
    fs:
        fsspec.filesystem instance (already connected)
    path:
        relative to fs
    metadata:
        current contents of metadata dict.
        Metadata obtained from fsurl will overwrite any similarly named fields in this dict
    fileset:
        Current contents of FILESET. new data will be appended.
        Similarly named entries will be overwritten.

    returns metadata dict
    """
    # There's a chance this should get rewritten to use 'fsspec.walk'

    if metadata is None:
        metadata = {}
    if fileset is None:
        fileset = metadata.get('fileset', {})
    protocol = fs.protocol
    dirs_done = []
    dirs = [path]

    while dirs:
        dirname = dirs.pop()
        rel_dirname = os.path.relpath(dirname, start=path)
        dirs_done.append(dirname)
        for file_info in fs.ls(dirname, detail=True):
            file_type = file_info.get('type', None)
            file_name = file_info['name']
            if file_type == 'directory':
                dirs.append(file_name)
            elif file_type == 'file':
                basename = os.path.basename(os.path.normpath(file_name))
                if str.isupper(basename):
                    # Add to metadata
                    with fs.open(file_name, 'r') as fr:
                        contents = '\n'.join(fr.readlines())
                    metadata[str.lower(basename)] = contents
                else:
                    # add file and hash to FILESET
                    if protocol == "abfs":
                        # Cheap way to get md5
                        md5_arr = file_info['content_settings']['content_md5']
                        hashval = f"md5:{''.join('{:02x}'.format(x) for x in md5_arr)}"
                    else:
                        logger.warning(f"Unsupported fsspec filesystem: {fs.protocol}. Using size as hash")
                        hashval = f"size:{fs.size(file_name)}"
                    rel_path = os.path.relpath(file_info['name'], start=dirname) or "."
                    # fileset[rel_dirname][rel_path] = [hashval]
                    entry = {rel_path:[hashval]}
                    fileset.setdefault(rel_dirname,{}).update(entry)
            else:
                raise Exception(f"Unknown file type: {file_type}")
    metadata["fileset"] = fileset
    return metadata



def dataset_from_fsurl(fsurl,
                       dataset_name=None,
                       fsspec_auth=None,
                       metadata=None,
                       fileset=None,
                       overwrite_catalog=True):
    """Create a dataset from the contents of an fsspec URL

    'fsurl' is assumed to be a directory/container/bucket.

    Files in this bucket with names entirely in UPPERCASE are assumed
    to be textfiles and are used to populate metadata fields directly
    as metadata fields (e.g. README, LICENSE)

    Other files have their hashes added to FILESET, and are included in
    the FileSet (FILESET data) associated with the dataset.

    Parameters::

    fsurl: fsspec URL
        Should be a "directory", container, or "subdirectory" of said container.
    dataset_name: string or None
        Name to use for Dataset.
        if None, name is the last component of the fsurl path
    metadata:
        current contents of metadata dict.
        Metadata obtained from fsurl will overwrite any similarly named fields in this dict
    fileset:
        Current contents of FILESET. new data will be appended.
        Similarly named entries will be overwritten.
    overwrite_catalog: Boolean
        if True, entry in Dataset catalog will be overwritten with the newly generated Dataset

    Returns::
    Dataset containing only metadata and FILESET info for all files in the specified fsspec URL.

    """
    if fsspec_auth is None:
        fsspec_auth = {}

    f = fsspec.open(fsurl, **fsspec_auth)
    path = f.path
    if dataset_name is None:
        dataset_name = os.path.basename(os.path.normpath(path))
        logger.debug(f"Inferring dataset_name from fsurl: {dataset_name}")
    fs = f.fs
    protocol = fs.protocol
    meta = metadata_from_fsspec(fs, path, metadata=metadata, fileset=fileset)
    meta['fileset_base'] = fsurl
    ds = dataset_from_metadata(dataset_name,
                               metadata=meta,
                               overwrite_catalog=overwrite_catalog)
    return ds

def derived_dataset(*, dataset_name, source_dataset, added_readme_txt=None, drop_fileset=True, data=None, target=None):
    """Create a dataset by copying its metadata from another dataset

    Parameters
    ----------
    added_readme_txt: string
        String to be appended to the end of the new dataset's README metadata
    drop_fileset: boolean
        if True, ignore fileset when copying metadata
    data:
        Will be used as contents of new dataset's `data`
    target:
        Will be used as contents of new dataset's `target`
    dataset_name: String
        new dataset name
    source_dataset: Dataset
        Metadata will be copied from this dataset

    Returns
    -------
    new (derived) Dataset object
    """
    new_metadata = ds.metadata.copy()
    if added_readme_txt:
        new_metadata['readme'] += added_readme_txt
    if drop_fileset:
        if new_metadata.get('fileset', 0) != 0:
            new_metadata.pop('fileset')
    if new_metadata.get('hashes', 0) != 0:
            new_metadata.pop('hashes')
    ds_out = Dataset(dataset_name, metadata=new_metadata, data=data, target=target, **kwargs)
    return ds_out
