import cv2
import glob
import logging
import os
import pathlib
import pandas as pd
import numpy as np
import json
from sklearn.datasets.base import Bunch
from scipy.io import loadmat
from functools import partial
import joblib
import sys

from .utils import fetch_and_unpack, get_dataset_filename
from ..paths import data_path, raw_data_path, interim_data_path, processed_data_path

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

def new_dataset(*, dataset_name):
    """Return an unpopulated dataset object.

    Fills in LICENSE and DESCR if they are present.
    Takes metadata from the url_list object if present. Otherwise, if
    `*.license` or `*.readme` files are present in the module directory,
    these will be as LICENSE and DESCR respectively.
    """
    global dataset_raw_files

    dset = Bunch()
    dset['metadata'] = {}
    dset['LICENSE'] = None
    dset['DESCR'] = None
    filemap = {
        'LICENSE': f'{dataset_name}.license',
        'DESCR': f'{dataset_name}.readme'
    }

    # read metadata from disk if present
    for metadata_type in filemap:
        metadata_file = _MODULE_DIR / filemap[metadata_type]
        if metadata_file.exists():
            with open(metadata_file, 'r') as fd:
                dset[metadata_type] = fd.read()

    # Use downloaded metadata if available
    ds = dataset_raw_files[dataset_name]
    for fetch_dict in ds.get('url_list', []):
        name = fetch_dict.get('name', None)
        # if metadata is present in the URL list, use it
        if name in ['DESCR', 'LICENSE']:
            txtfile = get_dataset_filename(fetch_dict)
            with open(raw_data_path / txtfile, 'r') as fr:
                dset[name] = fr.read()

    return dset

def add_dataset_by_urllist(dataset_name, url_list):
    """Add a new dataset by specifying a url_list

    url_list is a list of dicts keyed by:
        * url, hash_type, hash_value, name, file_name
    """
    global dataset_raw_files

    dataset_raw_files[dataset_name] = {'url_list': url_list}
    write_dataset()
    dataset_raw_files = read_datasets()
    return dataset_raw_files[dataset_name]

def add_dataset_metadata(dataset_name, from_file=None, from_str=None, kind='DESCR'):
    """Add metadata to a dataset

    from_file: create metadata entry from contents of this file
    from_str: create metadata entry from this string
    kind: {'DESCR', 'LICENSE'}
    """
    global dataset_raw_files

    filename_map = {
        'DESCR': f'{dataset_name}.readme',
        'LICENSE': f'{dataset_name}.license',
    }

    if dataset_name not in dataset_raw_files:
        raise Exception(f'No such dataset: {dataset_name}')

    if kind not in filename_map:
        raise Exception(f'Unknown kind: {kind}. Must be one of {filename_map.keys()}')

    if from_file is not None:
        with open(from_file, 'r') as fd:
            meta_txt = fd.read()
    elif from_str is not None:
        meta_txt = from_str
    else:
        raise Exception(f'One of `from_file` or `from_str` is required')

    with open(_MODULE_DIR / filename_map[kind], 'w') as fw:
        fw.write(meta_txt)

def load_dataset(dataset_name, return_X_y=False, force=False, **kwargs):
    '''Loads a scikit-learn style dataset

    dataset_name:
        Name of dataset to load
    return_X_y: boolean, default=False
        if True, returns (data, target) instead of a Bunch object
    force: boolean
        if True, do complete fetch/process cycle. If False, will use cached object (if present)
    '''

    if dataset_name not in dataset_raw_files:
        raise Exception(f'Unknown Dataset: {dataset_name}')

    # check for cached version
    cache_file = processed_data_path / f'{dataset_name}.jlib'
    if cache_file.exists() and force is not True:
        dset = joblib.load(cache_file)
    else:
        # no cache. Regenerate
        fetch_and_unpack(dataset_name)
        dset = dataset_raw_files[dataset_name]['load_function'](**kwargs)
        with open(cache_file, 'wb') as fo:
            joblib.dump(dset, fo)

    if return_X_y:
        return dset.data, dset.target
    else:
        return dset

def read_space_delimited(filename, skiprows=None, class_labels=True):
    """Read an space-delimited file

    skiprows: list of rows to skip when reading the file.

    Note: we can't use automatic comment detection, as
    `#` characters are also used as data labels.
    class_labels: boolean
        if true, the last column is treated as the class label
    """
    with open(filename, 'r') as fd:
        df = pd.read_table(fd, skiprows=skiprows, skip_blank_lines=True, comment=None, header=None, sep=' ', dtype=str)
        # targets are last column. Data is everything else
        if class_labels is True:
            target = df.loc[:,df.columns[-1]].values
            data = df.loc[:,df.columns[:-1]].values
        else:
            data = df.values
            target = np.zeros(data.shape[0])
        return data, target

def write_dataset(path=None, filename="datasets.json", indent=4, sort_keys=True):
    """Write a serialized (JSON) dataset file"""
    if path is None:
        path = _MODULE_DIR
    else:
        path = pathlib.Path(path)

    ds = dataset_raw_files.copy()
    # copy, adjusting non-serializable items
    for key, entry in ds.items():
        func = entry.get('load_function', None)
        if func is None:
             func = partial(new_dataset, dataset_name=key)
        else:
            del(entry['load_function'])
        entry['load_function_name'] = func.func.__name__
        entry['load_function_options'] = func.keywords
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
