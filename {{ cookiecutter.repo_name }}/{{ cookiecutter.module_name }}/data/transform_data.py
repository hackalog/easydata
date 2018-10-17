import logging
import os
import pathlib
import sys

from ..logging import logger
from ..utils import load_json, save_json
from .datasets import Dataset, RawDataset, available_raw_datasets
from .transformers import available_transformers
from ..paths import processed_data_path

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
        transformer_path = _MODULE_DIR
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

def add_transformer(from_raw=None, raw_dataset_opts=None,
                    input_dataset=None, suppress_output=False, output_dataset=None,
                    transformations=None,
                    transformer_path=None, transformer_file=None):
    """Create and add a dataset transformation pipeline to the workflow.

    Transformer pipelines apply a sequence of transformer functions to a Dataset (or RawDataset),
    producing a new Dataset.

    Parameters
    ----------
    input_dataset: string
        Name of a dataset_dir
        Specifying this option creates a dataset transformation pipeline that begins
        with an existing dataset_dir
    from_raw: string
        Name of a raw dataset.
        Specifying this option creates a dataset transformation pipeline that begins
        starts from a raw dataset with this namew
    output_dataset: string
        Name to use when writing the terminal Dataset object to disk.
    raw_dataset_opts: dict
        Options to use when generating raw dataset
    suppress_output: boolean
        If True, the terminal dataset object is not written to disk.
        This is useful when one of the intervening tranformers handles the writing; e.g. train/test split.
    transformeations: list of tuples
        Squence of transformer functions to apply. tuples consist of:
        (transformer_name, transformer_opts)
    transformer_path: path. (default: MODULE_DIR)
        Location of `transformer_file`
    transformer_file: string, default 'transformer_list.json'
        Name of json file that contains the transformer pipeline
    """

    if from_raw is not None and input_dataset is not None:
        raise Exception('Cannot set both `from_raw` and `input_datset`')
    if from_raw is None and raw_dataset_opts is not None:
        raise Exception('Must specify `from_raw` when using `raw_dataset_opts`')

    transformer_list, transformer_file_fq = get_transformer_list(transformer_path=transformer_path,
                                                                 transformer_file=transformer_file,
                                                                 include_filename=True)

    transformer = {}
    if from_raw:
        transformer['raw_dataset_name'] = from_raw
        if output_dataset is None and not suppress_output:
            output_dataset = from_raw
    elif input_dataset:
        transformer['input_dataset'] = input_dataset
    else:
        raise Exception("Must specify one of from `from_raw` or `input_dataset`")

    if raw_dataset_opts:
        transformer['raw_dataset_opts'] = raw_dataset_opts

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
        output_dir = processed_data_path
    else:
        output_dir = pathlib.Path(output_dir)

    if transformer_path is None:
        transformer_path = _MODULE_DIR
    else:
        transformer_path = pathlib.Path(transformer_path)

    transformer_list = get_transformer_list(transformer_path=transformer_path,
                                            transformer_file=transformer_file)
    raw_datasets = available_raw_datasets()
    transformers = available_transformers(keys_only=False)

    for tdict in transformer_list:
        raw_dataset_opts = tdict.get('raw_dataset_opts', {})
        raw_dataset_name = tdict.get('raw_dataset_name', None)
        output_dataset = tdict.get('output_dataset', None)
        input_dataset = tdict.get('input_dataset', None)
        transformations = tdict.get('transformations', [])
        if raw_dataset_name is not None:
            if raw_dataset_name not in raw_datasets:
                raise Exception(f"Unknown RawDataset: {raw_dataset_name}")
            logger.debug(f"Creating Dataset from Raw: {raw_dataset_name} with opts {raw_dataset_opts}")
            rds = RawDataset.from_name(raw_dataset_name)
            ds = rds.process(**raw_dataset_opts)
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
