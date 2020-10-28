## Script common ways of adding a dataset to the workflow

from functools import partial
import pathlib

from ..log import logger
from .. import paths, workflow

from . import DataSource, Dataset, hash_file, TransformerGraph, create_transformer_pipeline
from .transformer_functions import csv_to_pandas
from .extra import process_extra_files

# Create a Dataset from a single csv file
def dataset_from_csv_manual_download(ds_name, csv_path, download_message,
                                     license_str, descr_str, *, hash_type='sha1',
                                     hash_value=None,):
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
    """

    csv_path = pathlib.Path(csv_path)
    # Create a datasource
    raw_ds_name = ds_name+"_raw"
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
    workflow.add_datasource(dsrc)

    # Add a dataset from the datasource
    dag = TransformerGraph(catalog_path=paths['catalog_path'])
    dag.add_source(output_dataset=raw_ds_name, datasource_name=raw_ds_name, force=True)
    # Run the dataset creation code to add it to the catalog
    ds = Dataset.from_catalog(raw_ds_name)

    # Add transformer to create the final dataset
    transformers = [partial(csv_to_pandas,
                            output_map={ds_name:csv_path.name})]

    dag.add_edge(input_dataset=raw_ds_name,
                 output_dataset=ds_name,
                 transformer_pipeline=create_transformer_pipeline(transformers),
                 force=True)

    ds = Dataset.from_catalog(ds_name)
    return ds
