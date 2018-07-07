import logging
import os
import pathlib
import json
from sklearn.datasets.base import Bunch
from functools import partial
from joblib import Memory
import sys

from .utils import fetch_and_unpack
from ..paths import data_path, raw_data_path, interim_data_path, processed_data_path

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

jlmem = Memory(cachedir=str(interim_data_path))

@jlmem.cache
def load_dataset(dataset_name, return_X_y=False, **kwargs):
    '''Loads a scikit-learn style dataset

    dataset_name:
        Name of dataset to load
    return_X_y: boolean, default=False
        if True, returns (data, target) instead of a Bunch object
    '''

    if dataset_name not in dataset_raw_files:
        raise Exception(f'Unknown Dataset: {dataset_name}')

    fetch_and_unpack(dataset_name)

    dset = dataset_raw_files[dataset_name]['load_function'](**kwargs)

    if return_X_y:
        return dset.data, dset.target
    else:
        return dset

def write_dataset(path=None, filename="datasets.json", indent=4, sort_keys=True):
    """Write a serialized (JSON) dataset file"""
    if path is None:
        path = _MODULE_DIR
    else:
        path = pathlib.Path(path)

    ds = dataset_raw_files.copy()
    # copy, adjusting non-serializable items
    for key, entry in ds.items():
        func = entry['load_function']
        del(entry['load_function'])
        entry['load_function_name'] = func.func.__name__
        entry['load_function_options'] = func.keywords
    print(ds)
    with open(path / filename, 'w') as fw:
        json.dump(ds, fw, indent=indent, sort_keys=sort_keys)

def read_datasets(path=None, filename="datasets.json"):
    """Read the serialized (JSON) dataset list
    """
    if path is None:
        path = _MODULE_DIR
    else:
        path = pathlib.Path(path)

    with open(path / filename, 'r') as fr:
        ds = json.load(fr)

    # make the functions callable
    for dset_name, dset_opts in ds.items():
        opts = dset_opts.get('load_function_options', {})
        fail_func = partial(unknown_function, dset_opts['load_function_name'])
        func_name = getattr(_MODULE, dset_opts['load_function_name'], fail_func)
        func = partial(func_name, **opts)
        dset_opts['load_function'] = func

    return ds

def unknown_function(args, **kwargs):
    """Placeholder for unknown function_name"""
    raise Exception("Unknown function: {args}, {kwargs}")

dataset_raw_files = read_datasets()

available_datasets = tuple(dataset_raw_files.keys())
