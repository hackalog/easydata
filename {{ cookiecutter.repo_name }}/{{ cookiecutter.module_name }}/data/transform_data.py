import os
import pathlib
import sys

from ..log import logger
from ..utils import load_json, save_json
from .datasets import Dataset, DataSource, available_datasources
from .transformers import available_transformers
from .. import paths

__all__ = [
    'add_transformer',
    'apply_transforms',
    'del_transformer',
    'get_transformer_list',
]


_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

def get_transformer_list(transformer_path=None, transformer_file=None, include_filename=False):
    """Get the list of transformation pipelines

    Returns
    -------
    If include_filename is True:
        A tuple: (transformer_list, transformer_file_fq)
    else:
        transformer_list

    Parameters
    ----------
    include_filename: boolean
        if True, returns a tuple: (list, filename)
    transformer_path: path. (default: MODULE_DIR/data)
        Location of `transformer_file`
    transformer_file: string, default 'transformer_list.json'
        Name of json file that contains the transformer pipeline
    """
    if transformer_path is None:
        transformer_path = paths['catalog_path']
    else:
        transformer_path = pathlib.Path(transformer_path)
    if transformer_file is None:
        transformer_file = 'transformer_list.json'

    transformer_file_fq = transformer_path / transformer_file
    try:
        transformer_list = load_json(transformer_file_fq)
    except FileNotFoundError:
        transformer_list = []

    if include_filename:
        return transformer_list, transformer_file_fq
    return transformer_list

def del_transformer(index, transformer_path=None, transformer_file=None):
    """Delete an entry in the transformer list

    index: index of entry
    transformer_path: path. (default: MODULE_DIR)
        Location of `transformer_file`
    transformer_file: string, default 'transformer_list.json'
        Name of json file that contains the transformer pipeline
    """
    transformer_list, transformer_file_fq = get_transformer_list(transformer_path=transformer_path,
                                                                 transformer_file=transformer_file,
                                                                 include_filename=True)

    del(transformer_list[index])
    save_json(transformer_file_fq, transformer_list)

def add_transformer(from_datasource=None, datasource_opts=None,
                    input_dataset=None, suppress_output=False, output_dataset=None,
                    transformations=None,
                    transformer_path=None, transformer_file=None):
    """Create and add a dataset transformation pipeline to the workflow.

    Transformer pipelines apply a sequence of transformer functions to a Dataset (or DataSource),
    producing a new Dataset.

    Parameters
    ----------
    input_dataset: string
        Name of a dataset_dir
        Specifying this option creates a dataset transformation pipeline that begins
        with an existing dataset_dir
    from_datasource: string
        Name of a raw DataSource.
        Specifying this option creates a dataset transformation pipeline that begins
        starts from a raw dataset with this namew
    output_dataset: string
        Name to use when writing the terminal Dataset object to disk.
    datasource_opts: dict
        Options to use when generating raw dataset
    suppress_output: boolean
        If True, the terminal dataset object is not written to disk.
        This is useful when one of the intervening tranformers handles the writing; e.g. train/test split.
    transformations: list of tuples
        Squence of transformer functions to apply. tuples consist of:
        (transformer_name, transformer_opts)
    transformer_path: path. (default: MODULE_DIR)
        Location of `transformer_file`
    transformer_file: string, default 'transformer_list.json'
        Name of json file that contains the transformer pipeline
    """

    if from_datasource is not None and input_dataset is not None:
        raise Exception('Cannot set both `from_datasource` and `input_datset`')
    if from_datasource is None and datasource_opts is not None:
        raise Exception('Must specify `from_datasource` when using `datasource_opts`')

    transformer_list, transformer_file_fq = get_transformer_list(transformer_path=transformer_path,
                                                                 transformer_file=transformer_file,
                                                                 include_filename=True)

    transformer = {}
    if from_datasource:
        transformer['datasource_name'] = from_datasource
        if output_dataset is None and not suppress_output:
            output_dataset = from_datasource
    elif input_dataset:
        transformer['input_dataset'] = input_dataset
    else:
        raise Exception("Must specify one of from `from_datasource` or `input_dataset`")

    if datasource_opts:
        transformer['datasource_opts'] = datasource_opts

    if transformations:
        transformer['transformations'] = transformations

    if not suppress_output:
        if output_dataset is None:
            raise Exception("Must specify `output_dataset` (or use `suppress_output`")
        else:
            transformer['output_dataset'] = output_dataset

    transformer_list.append(transformer)
    save_json(transformer_file_fq, transformer_list)

def apply_transforms(transformer_path=None, transformer_file='transformer_list.json', output_dir=None):

    if output_dir is None:
        output_dir = paths['processed_data_path']
    else:
        output_dir = pathlib.Path(output_dir)

    if transformer_path is None:
        transformer_path = paths['catalog_path']
    else:
        transformer_path = pathlib.Path(transformer_path)

    transformer_list = get_transformer_list(transformer_path=transformer_path,
                                            transformer_file=transformer_file)
    datasources = available_datasources()
    transformers = available_transformers(keys_only=False)

    for tdict in transformer_list:
        datasource_opts = tdict.get('datasource_opts', {})
        datasource_name = tdict.get('datasource_name', None)
        output_dataset = tdict.get('output_dataset', None)
        input_dataset = tdict.get('input_dataset', None)
        transformations = tdict.get('transformations', [])
        if datasource_name is not None:
            if datasource_name not in datasources:
                raise Exception(f"Unknown DataSource: {datasource_name}")
            logger.debug(f"Creating Dataset from Raw: {datasource_name} with opts {datasource_opts}")
            rds = DataSource.from_name(datasource_name)
            ds = rds.process(**datasource_opts)
        else:
            logger.debug("Loading Dataset: {input_dataset}")
            ds = Dataset.load(input_dataset)

        for tname, topts in transformations:
            tfunc = transformers.get(tname, None)
            if tfunc is None:
                raise Exception(f"Unknwon transformer: {tname}")
            logger.debug(f"Applying {tname} to {ds.name} with opts {topts}")
            ds = tfunc(ds, **topts)

        if output_dataset is not None:
            logger.info(f"Writing transformed Dataset: {output_dataset}")
            ds.name = output_dataset
            ds.dump(dump_path=output_dir)
