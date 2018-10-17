import importlib
import os
import pathlib
import random
import sys
import pandas as pd
import numpy as np
from functools import partial
from joblib import func_inspect as jfi

from ..logging import logger

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
            target = df.loc[:, df.columns[-1]].values
            data = df.loc[:, df.columns[:-1]].values
        else:
            data = df.values
            target = np.zeros(data.shape[0])
        return data, target

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

def process_dataset_default(**kwargs):
    """Placeholder for data processing function"""
    logger.warning(f"Default `load_function` method. No `data` or `target` generated")
    return kwargs

def deserialize_partial(func_dict, delete_keys=False):
    """Convert a serialized function call into a partial

    Parameters
    ----------
    func_dict: dict containing
        load_function_name: function name
        load_function_module: module containing function
        load_function_args: args to pass to function
        load_function_kwargs: kwargs to pass to function
    """

    if delete_keys:
        args = func_dict.pop("load_function_args", [])
        kwargs = func_dict.pop("load_function_kwargs", {})
        base_name = func_dict.pop("load_function_name", 'process_dataset_default')
        func_mod_name = func_dict.pop('load_function_module', None)
    else:
        args = func_dict.get("load_function_args", [])
        kwargs = func_dict.get("load_function_kwargs", {})
        base_name = func_dict.get("load_function_name", 'process_dataset_default')
        func_mod_name = func_dict.get('load_function_module', None)

    fail_func = partial(process_dataset_default, dataset_name=base_name)

    if func_mod_name:
        func_mod = importlib.import_module(func_mod_name)
    else:
        func_mod = _MODULE
    func_name = getattr(func_mod, base_name, fail_func)
    func = partial(func_name, *args, **kwargs)

    return func

def serialize_partial(func):
    """Serialize a function call to a dictionary.

    Parameters
    ----------
    func: partial function.

    Returns
    -------
    dict containing:
        load_function_name: function name
        load_function_module: fully-qualified module name containing function
        load_function_args: args to pass to function
        load_function_kwargs: kwargs to pass to function
    """

    func = partial(func)
    entry = {}
    entry['load_function_module'] = ".".join(jfi.get_func_name(func.func)[0])
    entry['load_function_name'] = jfi.get_func_name(func.func)[1]
    entry['load_function_args'] = func.args
    entry['load_function_kwargs'] = func.keywords
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
