import logging
import os
import pathlib
import sys
import pandas as pd
import numpy as np
from functools import partial
from joblib import func_inspect as jfi

from ..paths import interim_data_path
from ..logging import logger

__all__ = [
    'head_file',
    'list_dir',
    'normalize_labels',
    'partial_call_signature',
    'read_space_delimited',
]

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

def head_file(filename, n=5):
    """Return the first `n` lines of a file
    """
    with open(filename, 'r') as fd:
        lines = []
        for i, line in enumerate(fd):
            if i > n:
                break
            lines.append(line)
    return "".join(lines)

def list_dir(path, fully_qualified=False, glob_pattern='*'):
    """do an ls on a path

    fully_qualified: boolean (default: False)
        If True, return a list of fully qualified pathlib objects.
        if False, return just the bare filenames
    glob_pattern: glob (default: '*')
        File mattern to match

    Returns
    -------
    A list of names, or fully qualified pathlib objects"""
    if fully_qualified:
        return list(pathlib.Path(path).glob(glob_pattern))

    return [file.name for file in pathlib.Path(path).glob(glob_pattern)]

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
    fq_keywords = {**default_kw, **fa.kwonlydefaults}
    return jfi.format_signature(func.func, *func.args, **fq_keywords)
