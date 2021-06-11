## Script common ways of adding a dataset to the workflow

from functools import partial
import pathlib

from .log import logger
from . import paths
from .exceptions import EasydataError

from .data import (DataSource, Dataset, hash_file, DatasetGraph, Catalog,
               serialize_transformer_pipeline)
from .data.transformer_functions import csv_to_pandas, new_dataset, apply_single_function, run_notebook_transformer
from .data.extra import process_extra_files
from .data.utils import serialize_partial

__all__ = [
    'notebook_as_transformer',
    'dataset_from_csv_manual_download',
    'dataset_from_metadata',
    'dataset_from_single_function',
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
                                     license_str, descr_str, *, hash_type='sha1',
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
    descr_str:
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
    dsrc.add_metadata(contents=descr_str, force=True)
    dsrc.add_metadata(contents=license_str, kind='LICENSE', force=True)

    process_function = process_extra_files
    process_function = process_extra_files
    process_function_kwargs = {'do_copy':True,
                               'file_glob':str(csv_path.name),
                               'extra_dir': raw_ds_name+'.extra',
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


def dataset_from_single_function(*, source_dataset_name, dataset_name, data_function, added_descr_txt, drop_extra=True, overwrite_catalog=False):
    """
    Create a derived dataset (dataset_name) via a single function call on .data from a
    previous dataset (source_dataset_name).

    Parameters
    ----------
    source_dataset_name:
        name of the dataset that the new dataset will be derived from
    dataset_name:
        name of the new dataset_catalog
    added_descr_txt: Default None
        new description text to be appended to the metadata descr
    data_function:
        function (from src module) to run on .data to produce the new .data
    overwrite_catalog: boolean
        if True, existing entries in datasets and transformers catalogs will be overwritten
    """
    dag = DatasetGraph(catalog_path=paths['catalog_path'])
    serialized_function = serialize_partial(data_function)
    transformers = [partial(apply_single_function, source_dataset_name=source_dataset_name, dataset_name=dataset_name,
                            serialized_function=serialized_function, added_descr_txt=added_descr_txt, drop_extra=drop_extra)]
    dag.add_edge(input_dataset=source_dataset_name,
                 output_dataset=dataset_name,
                 transformer_pipeline=serialize_transformer_pipeline(transformers),
                 overwrite_catalog=overwrite_catalog)
    ds = Dataset.from_catalog(dataset_name)
    logger.debug(f"{dataset_name} added to catalog")
    return ds
