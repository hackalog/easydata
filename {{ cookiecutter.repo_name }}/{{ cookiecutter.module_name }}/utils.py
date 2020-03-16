import time
import pathlib
import numpy as np
import json
from .log import logger
# Timing and Performance

def timing_info(method):
    def wrapper(*args, **kw):
        start_time = time.time()
        result = method(*args, **kw)
        end_time = time.time()
        logger.info(f"timing_info: {method.__name__}"
                    f"@{round((end_time-start_time)*1000,1)} ms")

        return result

    return wrapper

def record_time_interval(section, start_time, line_break=False):
    """Record a time interval since the last timestamp"""
    end_time = time.time()
    delta = end_time - start_time
    if delta < 1:
        delta *= 1000
        units = "ms"
    else:
        units = "s"
    if line_break:
        logger.debug("PROCESS_TIME:{:>36}    {} {}\n".format(section, round(delta, 1), units))
    else:
        logger.debug("PROCESS_TIME:{:>36}    {} {}".format(section, round(delta, 1), units))
    return end_time

def normalize_numpy_dict(d):
    ret = d.copy()
    for k, v in ret.items():
        if isinstance(v, np.generic):
            ret[k] = np.asscalar(v)
    return ret

def save_json(filename, obj, indent=2, sort_keys=True):
    """Dump an object to disk in json format

    filename: pathname
        Filename to dump to
    obj: object
        Object to dump
    indent: integer
        number of characters to indent
    sort_keys: boolean
        Whether to sort keys before writing. Should be True if you ever use revision control
        on the resulting json file.
    """
    with open(filename, 'w') as fw:
        json.dump(obj, fw, indent=indent, sort_keys=sort_keys)

def load_json(filename):
    """Read a json file from disk"""
    with open(filename) as fw:
        obj = json.load(fw)
    return obj

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
