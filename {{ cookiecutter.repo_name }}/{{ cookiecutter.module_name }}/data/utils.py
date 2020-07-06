import importlib
import os
import pathlib
import random
import sys
import pandas as pd
import numpy as np
from functools import partial
from joblib import func_inspect as jfi

from ..log import logger

__all__ = [
    'deserialize_partial',
    'normalize_labels',
    'partial_call_signature',
    'read_space_delimited',
    'reservoir_sample',
    'serialize_partial',
]

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

def read_space_delimited(filename, skiprows=None, class_labels=True, metadata=None):
    """Read an space-delimited file

    Data is space-delimited. Last column is the (string) label for the data

    Note: we can't use automatic comment detection, as `#` characters are also
    used as data labels.

    Parameters
    ----------
    skiprows: list-like, int or callable, optional
        list of rows to skip when reading the file. See `pandas.read_csv`
        entry on `skiprows` for more
    class_labels: boolean
        if true, the last column is treated as the class (target) label
    """
    with open(filename, 'r') as fd:
        df = pd.read_csv(fd, skiprows=skiprows, skip_blank_lines=True,
                           comment=None, header=None, sep=' ', dtype=str)
        # targets are last column. Data is everything else
        if class_labels is True:
            target = df.loc[:, df.columns[-1]].values
            data = df.loc[:, df.columns[:-1]].values
        else:
            data = df.values
            target = np.zeros(data.shape[0])
        return data, target, metadata

def normalize_labels(target):
    """Map an arbitary target vector to an integer vector

    Returns
    -------
    tuple: (mapped_target, label_map)

    where:
        mapped_target: integer vector of same shape as target
        label_map: dict mapping mapped_target integers to original labels

    Examples
    --------
    >>> target = np.array(['a','b','c','a'])
    >>> mapped_target, label_map = normalize_labels(target)
    >>> mapped_target
    array([0, 1, 2, 0])

    The following should always be true

    >>> all(np.vectorize(label_map.get)(mapped_target) == target)
    True
    """
    label_map = {k:v for k, v in enumerate(np.unique(target))}
    label_map_inv = {v:k for k, v in label_map.items()}
    mapped_target = np.vectorize(label_map_inv.get)(target)

    return mapped_target, label_map

def partial_call_signature(func):
    """Return the fully qualified call signature for a (partial) function
    """
    func = partial(func)
    fa = jfi.getfullargspec(func)
    default_kw = {}
    if fa.args:
        default_kw = dict(zip(fa.args, fa.defaults))
    if getattr(fa, 'kwonlydefaults', None):
        fq_keywords = {**default_kw, **fa.kwonlydefaults}
    else:
        fq_keywords = default_kw
    return jfi.format_signature(func.func, *func.args, **fq_keywords)

def process_dataset_default(metadata=None, **kwargs):
    """Placeholder for data processing function"""
    dataset_name = kwargs.get('dataset_name', 'unknown-dataset')
    logger.error(f"'{dataset_name}()' function not found. Define it add it to the `user` namespace for correct behavior")
    return None, None, metadata

def deserialize_partial(func_dict, delete_keys=False,
                        key_base='load_function',
                        fail_func=None):
    """Convert a serialized function call into a partial

    if there is an error, returns a default function (process_dataset_default)

    Parameters
    ----------
    func_dict: dict containing
        {key_base}_name: function name
        {key_base}_module: module containing function
        {key_base}_args: args to pass to function
        {key_base}_kwargs: kwargs to pass to function

    delete_keys: Boolean
        if True, keys are deleted from `func_dict` if found
    key_base: str
        name to be used when generating looking up keys in `func_dict`
    fail_func:
        function to use if no valid function found in the namespace

    """

    if delete_keys:
        args = func_dict.pop(f"{key_base}_args", [])
        kwargs = func_dict.pop(f"{key_base}_kwargs", {})
        base_name = func_dict.pop(f"{key_base}_name", 'process_dataset_default')
        func_mod_name = func_dict.pop(f'{key_base}_module', None)
    else:
        args = func_dict.get(f"{key_base}_args", [])
        kwargs = func_dict.get(f"{key_base}_kwargs", {})
        base_name = func_dict.get(f"{key_base}_name", 'process_dataset_default')
        func_mod_name = func_dict.get(f'{key_base}_module', None)

    if fail_func is None:
        fail_func = partial(process_dataset_default, dataset_name=base_name)

    try:
        if func_mod_name:
            func_mod = importlib.import_module(func_mod_name)
        else:
            func_mod = _MODULE
        func_name = getattr(func_mod, base_name, fail_func)
    except ModuleNotFoundError as e:
        logger.error(f"Invalid parse_function: {e}")
        func_name = fail_func
    func = partial(func_name, *args, **kwargs)

    return func

def serialize_partial(func, key_base='load_function'):
    """Serialize a function call to a dictionary.

    Parameters
    ----------
    func: function
        function to serialize
    key_base: str. Default 'load_function'
        string to prepend to serialization parameters.

    Returns
    -------
    dict containing:
        {key_base}_name: function name
        {key_base}_module: fully-qualified module name containing function
        {key_base}_args: args to pass to function
        {key_base}_kwargs: kwargs to pass to function
    """

    entry = {}
    if func is None:
        logger.warning(f"serialize_partial: `{key_base}` is None. Ignoring.")
        return entry
    func = partial(func)
    entry[f'{key_base}_module'] = ".".join(jfi.get_func_name(func.func)[0])
    entry[f'{key_base}_name'] = jfi.get_func_name(func.func)[1]
    entry[f'{key_base}_args'] = func.args
    entry[f'{key_base}_kwargs'] = func.keywords
    return entry

def reservoir_sample(filename, n_samples=1, random_seed=None):
    """Return a random subset of lines from a file

    Parameters
    ----------
    filename: path
        File to be loaded
    n_samples: int
        number of lines to return
    random_seed: int or None
        If set, use this as the random seed
    """
    if random_seed is not None:
        random.seed(random_seed)
    sample = []
    with open(filename) as f:
        for n, line in enumerate(f):
            if n < n_samples:
                sample.append(line.rstrip())
            else:
                r = random.randint(0, n_samples)
                if r < n_samples:
                    sample[r] = line.rstrip()
    return sample
