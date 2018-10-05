import joblib
import logging
import os
import pathlib
import sys
from sklearn.datasets.base import Bunch
from functools import partial

from ..paths import processed_data_path, data_path, raw_data_path, interim_data_path
from ..logging import logger
from .fetch import fetch_file, unpack, get_dataset_filename
from .utils import partial_call_signature

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

__all__ = ['Dataset', 'RawDataset']

def process_dataset_default(**kwargs):
    """Placeholder for data processing function"""
    logger.warning(f"No Processing function defined")
    return kwargs

class Dataset(Bunch):
    def __init__(self, dataset_name=None, data=None, target=None, metadata=None,
                 license_txt=None, descr_txt=None, license_file=None, descr_file=None,
                 **kwargs):
        """
        Object representing a dataset object.
        Notionally compatible with scikit-learn's Bunch object

        dataset_name: string (required)
            key to use for this dataset
        data:
            Data: (usually np.array or np.ndarray)
        target: np.array
            Either classification target or label to be used. for each of the points
            in `data`
        metadata: dict
            Data about the object. Key fields include `license_txt` and `descr`
        license_txt: str
            String to use as the LICENSE for this dataset
        license_file: filename
            If `license_txt` is None, license text can be read from this file
        descr_txt: str
            String to use as the DESCR (description) for this dataset
        descr_file: filename
            If `descr_txt` is None, description text can be read from this file

        """
        super().__init__(**kwargs)

        if dataset_name is None:
            if metadata is not None and metadata.get("dataset_name", None) is not None:
                dataset_name = metadata['dataset_name']
            else:
                raise Exception('dataset_name is required')

        if metadata is not None:
            self['metadata'] = metadata
        else:
            self['metadata'] = {}
        self['metadata']['dataset_name'] = dataset_name
        if license_file is not None:
            with open(license_file, 'r') as f:
                license_txt = f.read()
        if license_txt is not None:
            self['metadata']['license'] = license_txt
        if descr_file is not None:
            with open(descr_file, 'r') as f:
                descr_txt = f.read()
        if descr_txt is not None:
            self['metadata']['descr'] = descr_txt
        self['data'] = data
        self['target'] = target

    def __getattribute__(self, key):
        if key.isupper():
            try:
                return self['metadata'][key.lower()]
            except:
                raise AttributeError(key)
        else:
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        if key.isupper():
            self['metadata'][key.lower()] = value
        elif key == 'name':
            self['metadata']['dataset_name'] = value
        else:
            super().__setattr__(key, value)

    def __str__(self):
        s = f"<Dataset: {self.name}"
        if self.get('data', None) is not None:
            shape = getattr(self.data, 'shape', 'Unknown')
            s += f", data.shape={shape}"
        if self.get('target', None) is not None:
            shape = getattr(self.target, 'shape', 'Unknown')
            s += f", target.shape={shape}"
        meta = self.get('metadata', {})
        if meta:
            s += f", metadata={list(meta.keys())}"

        s += ">"
        return s

    @property
    def name(self):
        return self['metadata'].get('dataset_name', None)

    @property
    def has_target(self):
        return self['target'] is not None

    @classmethod
    def load(cls, file_base, data_path=None, metadata_only=False):
        """Load a dataset
        must be present in dataset.json"""

        if data_path is None:
            data_path = processed_data_path
        else:
            data_path = pathlib.Path(data_path)

        if metadata_only:
            metadata_fq = data_path / f'{file_base}.metadata'
            with open(metadata_fq, 'rb') as fd:
                meta = joblib.load(fd)
            return meta

        with open(data_path / f'{file_base}.dataset', 'rb') as fd:
            ds = joblib.load(fd)
        return ds

    def get_data_hashes(self, exclude_list=None, hash_type='sha1'):
        """Compute a the hash of data items

        exclude_list: list or None
            List of attributes to skip.
            if None, skips ['metadata']

        hash_type: {'sha1', 'md5', 'sha256'}
            Algorithm to use for hashing
        """
        if exclude_list is None:
            exclude_list = ['metadata']

        ret = {'hash_type': hash_type}
        for key, value in self.items():
            if key in exclude_list:
                continue
            ret[f"{key}_hash"] = joblib.hash(value, hash_name=hash_type)
        return ret

    def dump(self, file_base=None, data_path=None, hash_type='sha1',
             force=True, create_dirs=True, dump_metadata=True):
        """Dump a dataset.

        Note, this dumps a separate metadata structure, so that dataset

        dump_metadata: boolean
            If True, also dump a standalone copy of the metadata.
            Useful for checking metadata without reading
            in the (potentially large) dataset itself
        file_base: string
            Filename stem. By default, just the dataset name
        hash_type: {'sha1', 'md5'}
            Hash function to use for hashing data/labels
        data_path: path. (default: `processed_data_path`)
            Directory where data will be dumped.
        force: boolean
            If False, raise an exception if the file already exists
            If True, overwrite any existing files
        create_dirs: boolean
            If True, `data_path` will be created (if necessary)

        """
        if data_path is None:
            data_path = processed_data_path
        data_path = pathlib.Path(data_path)

        if file_base is None:
            file_base = self.name

        metadata = self['metadata']

        metadata_filename = file_base + '.metadata'
        dataset_filename = file_base + '.dataset'
        metadata_fq = data_path / metadata_filename

        data_hashes = self.get_data_hashes(hash_type=hash_type)
        self['metadata'] = {**self['metadata'], **data_hashes}

        # check for a cached version
        if metadata_fq.exists() and force is not True:
            logger.warning(f"Existing metatdata file found: {metadata_fq}")
            cached_metadata = joblib.load(metadata_fq)
            # are we a subset of the cached metadata? (Py3+ only)
            if metadata.items() <= cached_metadata.items():
                raise Exception(f'Dataset with matching metadata exists already. '
                                'Use `force=True` to overwrite, or change one of '
                                '`dataset.metadata` or `file_base`')
            else:
                raise Exception(f'Metadata file {metadata_filename} exists '
                                'but metadata has changed. '
                                'Use `force=True` to overwrite, or change '
                                '`file_base`')

        if create_dirs:
            os.makedirs(metadata_fq.parent, exist_ok=True)

        if dump_metadata:
            with open(metadata_fq, 'wb') as fo:
                joblib.dump(metadata, fo)
            logger.debug(f'Wrote {metadata_filename}')

        dataset_fq = data_path / dataset_filename
        with open(dataset_fq, 'wb') as fo:
            joblib.dump(self, fo)
        logger.debug(f'Wrote {dataset_filename}')

class RawDataset(object):
    """Representation of a raw dataset"""

    def __init__(self,
                 name='raw_dataset',
                 load_function=None,
                 dataset_dir=None,
                 file_list=None):
        if file_list is None:
            file_list = []
        if dataset_dir is None:
            dataset_dir = data_path
        if load_function is None:
            load_function = process_dataset_default
        self.name = name
        self.file_list = file_list
        self.load_function = load_function
        self.dataset_dir = dataset_dir

        # sklearn-style attributes. Usually these would be set in fit()
        self.fetched_ = False
        self.fetched_files_ = []
        self.unpacked_ = False

    def add_url(self, url=None, hash_type='sha1', hash_value=None,
                name=None, file_name=None):
        """
        Add a URL to the file list

        hash_type: {'sha1', 'md5', 'sha256'}
        hash_value: string or None
            if None, hash will be computed from downloaded file
        file_name: string or None
            Name of downloaded file. If None, will be the last component of the URL
        url: string
            URL to fetch
        file_name: string or None
            Name of downloaded file. If None, will be the last component of the URL
        name: str
            text description of this file.
        """

        fetch_dict = {'url': url,
                      'hash_type':hash_type,
                      'hash_value':hash_value,
                      'name': name,
                      'file_name':file_name}
        self.file_list.append(fetch_dict)

    def fetch(self, fetch_path=None, force=False):
        """Fetch to raw_data_dir and check hashes
        """
        if self.fetched_ and force is False:
            logger.debug(f'Raw Dataset {self.name} is already fetched. Skipping')
            return

        if fetch_path is None:
            fetch_path = raw_data_path

        self.fetched_ = False
        self.fetched_files_ = []
        for item in self.file_list:
            status, result, hash_value = fetch_file(**item)
            if status:
                item['hash_value'] = hash_value
                self.fetched_files_.append(result)
            else:
                if item.get('url', False):
                    logger.error(f"fetch of {item['url']} returned: {result}")
                    break
        else:
            self.fetched_ = True

        return self.fetched_


    def unpack(self, unpack_path=None, force=False):
        """Unpack fetched files to interim dir"""
        if not self.fetched_:
            raise Exception("Must fetch before unpack")

        if self.unpacked_ and force is False:
            logger.debug(f'Raw Dataset {self.name} is already unpacked. Skipping')
            return

        if unpack_path is None:
            unpack_path = interim_data_path
        for filename in self.fetched_files_:
            unpack(filename, dst_dir=unpack_path)
        self.unpacked_ = True


    def process(self, cache_dir=None, force=False, use_docstring=False, **kwargs):
        """Turns the raw dataset into a fully-processed Dataset object

        Parameters
        ----------
        return_X_y: boolean, default=False
            if True, returns (data, target) instead of a `Dataset` object.
        force: boolean
            If False, use a cached object (if available).
            If True, regenerate object from scratch.
        cache_dir: path
            Location of joblib cache.
        use_docstring: boolean
            If True, the docstring of `self.load_function` is used as the Dataset DESCR text.
        """

        if not self.unpacked_:
            raise Exception("Must fetch/unpack before process")

        if cache_dir is None:
            cache_dir = interim_data_path

        cached_meta = {
            'dataset_name': self.name,
            **kwargs
        }
        meta_hash = joblib.hash(cached_meta, hash_name='sha1')

        dset = None
        if force is False:
            try:
                dset = Dataset.load(meta_hash, data_path=cache_dir)
                logger.debug(f"Found cached Dataset for {self.name}: {meta_hash}")
            except FileNotFoundError:
                logger.debug(f"No cached Dataset found. Re-creating {self.name}")

        if dset is None:
            metadata = self.default_metadata(use_docstring=use_docstring)
            supplied_metadata = kwargs.pop('metadata', {})
            kwargs['metadata'] = {**metadata, **supplied_metadata}
            dset_opts = self.load_function(**kwargs)

        return dset_opts

    def default_metadata(self, use_docstring=False):
        """Returns default metatada derived from this RawDataset

        This sets the dataset_name, and fills in `license` and `descr`
        fields if they are present, either on disk, or in the file list

        Parameters
        ----------
        use_docstring: boolean
            If True, the docstring of `self.load_function` is used as the Dataset DESCR text.

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
            'license': f'{self.name}.license',
            'descr': f'{self.name}.readme'
        }

        for fetch_dict in self.file_list:
            name = fetch_dict.get('name', None)
            # if metadata is present in the URL list, use it
            if name in optmap:
                txtfile = get_dataset_filename(fetch_dict)
                with open(raw_data_path / txtfile, 'r') as fr:
                    metadata[optmap[name]] = fr.read()
        if use_docstring:
            func = partial(self.load_function)
            fqfunc, invocation =  partial_call_signature(func)
            metadata['descr'] =  f'Data processed by: {fqfunc}\n\n>>> ' + \
              f'{invocation}\n\n>>> help({func.func.__name__})\n\n' + \
              f'{func.func.__doc__}'
        else:
            descr_txt = None

        metadata['dataset_name'] = self.name
        return metadata

    def save(self, path=None, filename="datasets.json", indent=4, sort_keys=True):
        pass

    @classmethod
    def load(cls, filename="raw_dataset.json", path=None):
        """Create a RawDataset from a (saved) json file.
        """
        if path is None:
            path = _MODULE_DIR
        else:
            path = pathlib.Path(path)

        with open(path / filename, 'r') as fr:
            ds = json.load(fr)

        load_function = deserialize_partial(**ds)

        return cls(**ds)

def deserialize_partial(func_dict):
    """Convert a serialized function call into a partial

    Parameters
    ----------
    func_dict: dict containing
        load_function_name: function name
        load_function_module: module containing function
        load_function_args: args to pass to function
        load_function_kwargs: kwargs to pass to function
    """

    args = func_dict.get("load_function_args", [])
    kwargs = func_dict.get("load_function_kwargs", {})
    base_name = func_dict.get("load_function_name", 'unknown_function')
    fail_func = partial(unknown_function, base_name)
    func_mod_name = func_dict.get('load_function_module', None)
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
