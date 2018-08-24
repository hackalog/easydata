from functools import partial
import importlib
import joblib
import joblib.func_inspect as jfi
import json
import logging
import os
import pathlib
import requests
import sys

from .dset import Dataset
from .utils import hash_file, unpack, hash_function_map, read_space_delimited, normalize_labels
from ..paths import data_path, raw_data_path, interim_data_path, processed_data_path
from .localdata import *

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

jlmem = joblib.Memory(cachedir=str(interim_data_path), verbose=0)

def get_default_metadata(*, dataset_name):
    """Create default metatada for a dataset.

    This sets the dataset_name, and fills in `license` and `descr`
    fields if they are present, either on disk, or in the datasets.json

    Returns
    -------
    Dict of metadata key/value pairs
    """

    metadata = {}
    optmap = {
        'DESCR': 'descr',
        'LICENSE': 'license',
    }
    filemap = {
        'license': f'{dataset_name}.license',
        'descr': f'{dataset_name}.readme'
    }

    # read metadata from disk if present
    for key in filemap:
        metadata_file = _MODULE_DIR / filemap[key]
        if metadata_file.exists():
            with open(metadata_file, 'r') as fd:
                metadata[key] = fd.read()

    # Use downloaded metadata if available
    dslist = read_datasets()
    ds = dslist.get(dataset_name, {})
    for fetch_dict in ds.get('url_list', []):
        name = fetch_dict.get('name', None)
        # if metadata is present in the URL list, use it
        if name in ['DESCR', 'LICENSE']:
            txtfile = get_dataset_filename(fetch_dict)
            with open(raw_data_path / txtfile, 'r') as fr:
                metadata[optmap[name]] = fr.read()

    metadata['dataset_name'] = dataset_name
    return metadata

def new_dataset(metadata=None, *, dataset_name):
    if metadata is None:
        metadata = get_default_metadata(dataset_name=dataset_name)
    return Dataset(metadata=metadata)


def get_dataset_filename(ds_dict):
    '''Figure out the downloaded filename for a dataset entry

    if a `file_name` key is present, use this,
    otherwise, use the last component of the `url`

    Returns the filename
    '''

    file_name = ds_dict.get('file_name', None)
    url = ds_dict.get('url', [])
    if file_name is None:
        file_name = url.split("/")[-1]
    return file_name

def fetch_files(force=False, dst_dir=None, **kwargs):
    '''
    fetches a list of files via URL

    url_list: list of dicts, each containing:
        url:
            url to be downloaded
        hash_type:
            Type of hash to compute
        hash_value: (optional)
            if specified, the hash of the downloaded file will be
            checked against this value
        name: (optional)
            Name of this dataset component
        raw_file:
            output file name. If not specified, use the last
            component of the URL
    '''
    url_list = kwargs.get('url_list', None)
    if not url_list:
        return fetch_file(force=force, dst_dir=dst_dir, **kwargs)
    result_list = []
    for url_dict in url_list:
        name = url_dict.get('name', 'dataset')
        logger.info(f"Fetching {name}")
        result_list.append(fetch_file(force=force, dst_dir=dst_dir, **url_dict))
    return all([r[0] for r in result_list]), result_list

def fetch_text_file(url, file_name=None, dst_dir=None, force=True, **kwargs):
    """Fetch a text file (via URL) and return it as a string.

    Arguments
    ---------

    file_name:
        output file name. If not specified, use the last
        component of the URL
    dst_dir:
        directory to place downloaded files
    force: boolean
        normally, the URL is only downloaded if `file_name` is
        not present on the filesystem, or if the existing file has a
        bad hash. If force is True, download is always attempted.

    In addition to these options, any of `fetch_file`'s keywords may
    also be passed

    Returns
    -------
    fetched string, or None if something went wrong with the download
    """
    retlist = fetch_file(url, file_name=file_name, dst_dir=dst_dir,
                         force=force, **kwargs)
    if retlist[0]:
        status, filename, hashval = retlist
        with open(filename, 'r') as txt:
            return txt.read()
    else:
        logger.warning(f'fetch of {url} failed with status: {retlist[0]}')
        return None

def fetch_file(url=None, contents=None,
               file_name=None, dst_dir=None,
               force=False,
               hash_type="sha1", hash_value=None,
               **kwargs):
    '''Fetch remote files via URL

    contents:
        contents of file to be created
    url:
        url to be downloaded
    hash_type:
        Type of hash to compute
    hash_value: (optional)
        if specified, the hash of the downloaded file will be
        checked against this value
    name: (optional)
        Name of this dataset component
    file_name:
        output file name. If not specified, use the last
        component of the URL
    dst_dir:
        directory to place downloaded files
    force: boolean
        normally, the URL is only downloaded if `file_name` is
        not present on the filesystem, or if the existing file has a
        bad hash. If force is True, download is always attempted.


    returns one of:


        (HTTP_Code, downloaded_filename, hash) (if downloaded from URL)
        (True, filename, hash) (if already exists)
        (False, [error])
    if `file_name` already exists, compute the hash of the on-disk file,
    '''
    if dst_dir is None:
        dst_dir = raw_data_path
    if file_name is None:
        file_name = url.split("/")[-1]
    dl_data_path = pathlib.Path(dst_dir)

    if not os.path.exists(dl_data_path):
        os.makedirs(dl_data_path)

    raw_data_file = dl_data_path / file_name

    if raw_data_file.exists():
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        if hash_value is not None:
            if raw_file_hash == hash_value:
                if force is False:
                    logger.info(f"{file_name} exists and hash is valid")
                    return True, raw_data_file, raw_file_hash
            else:
                logger.warning(f"{file_name} exists but has bad hash {raw_file_hash}."
                               " Re-downloading")
        else:
            if force is False:
                logger.info(f"{file_name} exists, but no hash to check")
                return True, raw_data_file, raw_file_hash

    if url is None and contents is None:
        raise Exception("One of `url` or `contents` must be specified if `file_name` doesn't yet exist")

    if url is not None:
        # Download the file
        try:
            results = requests.get(url)
            results.raise_for_status()
            raw_file_hash = hash_function_map[hash_type](results.content).hexdigest()
            if hash_value is not None:
                if raw_file_hash != hash_value:
                    print(f"Invalid hash on downloaded {file_name}"
                          f" ({hash_type}:{raw_file_hash}) != {hash_type}:{hash_value}")
                    return False, None, raw_file_hash
            logger.info(f"Writing {raw_data_file}")
            with open(raw_data_file, "wb") as code:
                code.write(results.content)
        except requests.exceptions.HTTPError as err:
            return False, err, None
    elif contents is not None:
        with open(raw_data_file, 'w') as fw:
            fw.write(contents)
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        return True, raw_data_file, raw_file_hash
    else:
        raise Exception('One of `url` or `contents` must be specified')

    return results.status_code, raw_data_file, raw_file_hash

def build_dataset_dict(hash_type='sha1', hash_value=None, url=None,
                       name=None, file_name=None, from_txt=None):
    """fetch a URL, return a dataset dictionary entry

    hash_type: {'sha1', 'md5', 'sha256'}
    hash_value: string or None
        if None, hash will be computed from downloaded file
    file_name: string or None
        Name of downloaded file. If None, will be the last component of the URL
    url: string
        URL to fetch
    from_txt: string
        contents of file to create.
        One of `url` or `from_txt` must be specified

    returns: dict
    """
    if url is not None:
        fetch_dict = {'url': url, 'hash_type':hash_type, 'hash_value':hash_value, 'name': name, 'file_name':file_name}
    elif from_txt is not None:
        fetch_dict = {'contents': from_txt, 'name':name, 'file_name': file_name, 'hash_type': hash_type}
    else:
        fetch_dict = {'name':name, 'file_name': file_name, 'hash_type': hash_type}

    status, path, hash_value = fetch_files(**fetch_dict)
    if status:
        fetch_dict['hash_value'] = hash_value
        return fetch_dict

    if url:
        raise Exception(f"fetch of {url} returned status: {status}")

    raise Exception(f"creation of {file_name} failed")


def fetch_and_unpack(dataset_name, do_unpack=True):
    '''Fetch and process datasets to their usable form

    dataset_name: string
        Name of dataset. Must be in `datasets.json`
    do_unpack: boolean
        If false, just download, don't process.

    '''
    ds = read_datasets()
    if dataset_name not in ds:
        raise Exception(f"Unknown Dataset: {dataset_name}")

    interim_dataset_path = interim_data_path / dataset_name

    logger.info(f"Checking for {dataset_name}")
    if ds[dataset_name].get('url_list', None):
        single_file = False
        status, results = fetch_files(dst_dir=raw_data_path,
                                      **ds[dataset_name])
        if status:
            logger.info(f"Retrieved Dataset successfully")
        else:
            logger.error(f"Failed to retrieve all data files: {results}")
            raise Exception("Failed to retrieve all data files")
        if do_unpack:
            for _, filename, _ in results:
                unpack(filename, dst_dir=interim_dataset_path)
    else:
        single_file = True
        status, filename, hashval = fetch_file(dst_dir=raw_data_path,
                                               **ds[dataset_name])
        hashtype = ds[dataset_name].get('hash_type', None)
        if status:
            logger.info(f"Retrieved Dataset: {dataset_name} "
                        f"({hashtype}: {hashval})")
        else:
            logger.error(f"Unpack to {filename} failed (hash: {hashval}). "
                         f"Status: {status}")
            raise Exception(f"Failed to download raw data: {filename}")
        if do_unpack:
            unpack(filename, dst_dir=interim_dataset_path)
    if do_unpack:
        return interim_dataset_path
    if single_file:
        return filename
    return raw_data_path

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
        args = dset_opts.get('load_function_args', {})
        kwargs = dset_opts.get('load_function_kwargs', {})
        fail_func = partial(unknown_function, dset_opts['load_function_name'])
        func_mod_name = dset_opts.get('load_function_module', None)
        if func_mod_name:
            func_mod = importlib.import_module(func_mod_name)
        else:
            func_mod = _MODULE
        func_name = getattr(func_mod, dset_opts['load_function_name'], fail_func)
        func = partial(func_name, *args, **kwargs)
        dset_opts['load_function'] = func

    return ds

def unknown_function(args, **kwargs):
    """Placeholder for unknown function_name"""
    raise Exception(f"Unknown function: {args}, {kwargs}")

def write_datasets(ds, path=None, filename="datasets.json", indent=4, sort_keys=True):
    """Write a serialized (JSON) dataset file

    Converts the callable `load_function` into something that can be
    serialized to json"""
    if path is None:
        path = _MODULE_DIR
    else:
        path = pathlib.Path(path)
    # copy, adjusting non-serializable items
    for key, entry in ds.items():
        action = entry.get('action', 'fetch_and_process')
        entry['action'] = action
        func = entry.get('load_function', None)
        if func is None:
            if action == 'fetch_and_process':
                func = partial(new_dataset, dataset_name=key)
            elif action == 'generate':
                raise Exception('must specify generation function')
            else:
                raise Exception(f'Unknown action: {action}')
        else:
            del(entry['load_function'])
        entry['load_function_module'] = ".".join(jfi.get_func_name(func.func)[0])
        entry['load_function_name'] = jfi.get_func_name(func.func)[1]
        entry['load_function_args'] = func.args
        entry['load_function_kwargs'] = func.keywords

    with open(path / filename, 'w') as fw:
        json.dump(ds, fw, indent=indent, sort_keys=sort_keys)

def add_dataset_by_urllist(dataset_name, url_list, action="fetch_and_process"):
    """Add a new dataset by specifying a url_list

    action: {'fetch_and_process', 'generate'}
        Whether to download (natural data) or generate (synthetic data) this dataset
    url_list is a list of dicts keyed by:
        * url, hash_type, hash_value, name, file_name
    """

    dataset_list = read_datasets()
    dataset_list[dataset_name] = {'url_list': url_list, 'action': action}
    write_datasets(dataset_list)
    dataset_list = read_datasets()
    return dataset_list[dataset_name]

def add_dataset_metadata(dataset_name, from_file=None, from_str=None, kind='DESCR'):
    """Add metadata to a dataset

    from_file: create metadata entry from contents of this file
    from_str: create metadata entry from this string
    kind: {'DESCR', 'LICENSE'}
    """
    filename_map = {
        'DESCR': f'{dataset_name}.readme',
        'LICENSE': f'{dataset_name}.license',
    }
    ds_list = read_datasets()

    if dataset_name not in ds_list:
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

def add_dataset_from_function(dataset_name, function, action='fetch_and_process'):
    """Add a load function for the given dataset_name

    action: {'fetch_and_process', 'generate'}
        if `fetch_and_process`, data will be downloaded and then processed with this function.
        if `generate`, this function will be used to generate the data, and the function
            docstring will be used as the dataset description
    """
    ds_list = read_datasets()
    if ds_list.get(dataset_name) is None:
        ds_list[dataset_name] = {}
    ds_list[dataset_name]['load_function'] = partial(function)
    ds_list[dataset_name]['action'] = action
    write_datasets(ds_list)
    ds_list = read_datasets()

    return ds_list[dataset_name]

def generate_synthetic_dataset_opts(dataset_name, func, use_docstring=True):
    """Generate synthetic dataset options dict from a (partial) function

    dataset_name: string
        dataset name
    func: partial function returning 2- or 3-tuple
        (X, t) or (X, t, metadata)
    use_docstring: boolean
        If True, generate DECSR text consisting of the complete function signature
        and docstring of underlying generation function.

    Returns
    -------
    Dataset options dictionary conforming constructor signature of `Dataset`

    """
    func = partial(func)
    tup = func()
    if len(tup) == 2:
        X, t = tup
        metadata = {}
    elif len(tup) == 3:
        X, t, metadata = tup
    else:
        raise Exception(f"Unexpected number of parameters from {func}. Got {len(tup)}.")
    metadata['dataset_name'] = dataset_name
    if use_docstring:
        fqfunc, invocation =  jfi.format_signature(func.func, *func.args, **func.keywords)
        descr_txt =  f'Synthetic data produced by: {fqfunc}\n\n>>> {invocation}\n\n>>> help({func.func.__name__})\n\n{func.func.__doc__}'
    else:
        descr_txt = None

    ds_opts = {
        'dataset_name': dataset_name,
        'data': X,
        'target': t,
        'descr_txt': descr_txt,
        'metadata': metadata
    }
    return ds_opts

def load_dataset(dataset_name, return_X_y=False, map_labels=False, **kwargs):

    '''Loads a scikit-learn style dataset

    Parameters
    ----------
    dataset_name:
        Name of dataset to load. see `available_datasets.keys()` for the current list
    map_labels: boolean
        If true, target will be converted to an integer vector, and a label_map
        will be added to the metadata mapping back to the original labels)
    return_X_y: boolean, default=False
        if True, returns (data, target) instead of a `Dataset` object
    '''
    dataset_list = read_datasets()

    if dataset_name not in dataset_list:
        raise Exception(f'Unknown Dataset: {dataset_name}')
    action = dataset_list[dataset_name]['action']
    if action == 'generate':
        func = partial(dataset_list[dataset_name]['load_function'], **kwargs)
        dset_opts = generate_synthetic_dataset_opts(dataset_name, func)
    elif action == 'fetch_and_process':
        fetch_and_unpack(dataset_name)
        metadata = get_default_metadata(dataset_name=dataset_name)
        supplied_metadata = kwargs.pop('metadata', {})
        kwargs['metadata'] = {**metadata, **supplied_metadata}
        dset_opts = dataset_list[dataset_name]['load_function'](**kwargs)
    else:
        raise Exception(f"Unknown action: {action} for dataset: {dataset_name}")
    dset = Dataset(**dset_opts)

    if map_labels:
        if dset.metadata.get('label_map', None) is not None:
            raise Exception("label_map already present in dataset")
        mapped_target, label_map = normalize_labels(dset.target)
        dset.metadata['label_map'] = label_map
        dset.target = mapped_target

    if return_X_y:
        return dset.data, dset.target

    return dset

def available_datasets(action=None):
    """Returns the list of available datasets

    action: None, or one of {'fetch_and_process', 'generate'}
        If None, return all datasets
        Otherwise, filter results to datasets with the indicated `action`
    """
    if action is None:
        return list(read_datasets().keys())

    return [k for k, v in read_datasets().items() if v.get('action', None) == action]
