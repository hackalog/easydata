import os
import pathlib
import sys

import joblib
from sklearn.utils import Bunch
from sklearn.model_selection import train_test_split
from functools import partial
from .. import paths
from ..log import logger
from .fetch import fetch_file,  get_dataset_filename, hash_file, unpack, infer_filename
from .utils import partial_call_signature, serialize_partial, deserialize_partial, process_dataset_default
from ..utils import load_json, save_json

__all__ = [
    'Dataset',
    'DataSource',
    'add_datasource',
    'del_datasource',
    'available_datasets',
    'available_datasources',
    'process_datasources',
]

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

def available_datasets(dataset_path=None, keys_only=True):
    """Get a list of available datasets.

    Parameters
    ----------
    dataset_path: path
        location of saved dataset files
    """
    if dataset_path is None:
        dataset_path = paths['processed_data_path']
    else:
        dataset_path = pathlib.Path(dataset_path)

    ds_dict = {}
    for dsfile in dataset_path.glob("*.metadata"):
        ds_stem = str(dsfile.stem)
        ds_meta = Dataset.load(ds_stem, data_path=dataset_path, metadata_only=True)
        ds_dict[ds_stem] = ds_meta

    if keys_only:
        return list(ds_dict.keys())
    return ds_dict


def process_datasources(datasources=None, action='process'):
    """Fetch, Unpack, and Process data sources.

    Parameters
    ----------
    datasources: list or None
        List of data source names to process.
        if None, loops over all available data sources.
    action: {'fetch', 'unpack', 'process'}
        Action to perform on data sources:
            'fetch': download raw files
            'unpack': unpack raw files
            'process': generate and cache Dataset objects
    """
    if datasources is None:
        datasources = available_datasources()

    for dataset_name in datasources:
        dsrc = DataSource.from_name(dataset_name)
        logger.info(f'Running {action} on {dataset_name}')
        if action == 'fetch':
            dsrc.fetch()
        elif action == 'unpack':
            dsrc.unpack()
        elif action == 'process':
            ds = dsrc.process()
            logger.info(f'{dataset_name}: processed data has shape:{ds.data.shape}')

def add_datasource(rawds):
    """Add a data source to the list of available data sources"""

    rawds_list, rds_file_fq = available_datasources(keys_only=False)
    rawds_list[rawds.name] = rawds.to_dict()
    save_json(rds_file_fq, rawds_list)

def del_datasource(key):
    """Delete an entry in the datasource dict

    key: name of data source to delete
    """
    datasource_list, datasource_file_fq = available_datasources(keys_only=False)

    del(datasource_list[key])
    save_json(datasource_file_fq, datasource_list)

def available_datasources(datasource_file='datasources.json',
                           datasource_path=None, keys_only=True):
    """Returns the list of available datasets.

    Instructions for creating DataSources is stored in `datasources.json` by default.

    keys_only: boolean
        if True, return a list of available datasets (default)
        if False, return complete dataset dictionary and filename

    Returns
    -------
    If `keys_only` is True:
        List of available dataset names
    else:
        Tuple (available_datasource_dict, available_datasource_dict_filename)
    """
    if datasource_path is None:
        datasource_path = paths['catalog_path']

    datasource_file_fq = pathlib.Path(datasource_path) / datasource_file

    if not datasource_file_fq.exists():
        datasource_dict = {}
        logger.warning(f"No dataset file found: {datasource_file}")
    else:
        datasource_dict = load_json(datasource_file_fq)

    if keys_only:
        return list(datasource_dict.keys())

    return datasource_dict, datasource_file_fq


class Dataset(Bunch):
    def __init__(self, dataset_name=None, data=None, target=None, metadata=None, update_hashes=True,
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
        update_hashes:
            If True, update the data/target hashes in the Metadata.
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
        self['data'] = data
        self['target'] = target
        if update_hashes:
            data_hashes = self.get_data_hashes()
            self['metadata'] = {**self['metadata'], **data_hashes}

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

    @name.setter
    def name(self, val):
        self['metadata']['dataset_name'] = val

    @property
    def has_target(self):
        return self['target'] is not None

    @classmethod
    def load(cls, file_base, data_path=None, metadata_only=False):
        """Load a dataset
        must be present in dataset.json"""

        if data_path is None:
            data_path = paths['processed_data_path']
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

    @classmethod
    def from_datasource(cls, dataset_name,
                        cache_path=None,
                        fetch_path=None,
                        force=False,
                        unpack_path=None,
                        **kwargs):
        '''Creates Dataset object from a named DataSource.

        Dataset will be cached after creation. Subsequent calls with matching call
        signature will return this cached object.

        Parameters
        ----------
        dataset_name:
            Name of dataset to load. see `available_datasources()` for the current list
        cache_path: path
            Directory to search for Dataset cache files
        fetch_path: path
            Directory to download raw files into
        force: boolean
            If True, always regenerate the dataset. If false, a cached result can be returned
        unpack_path: path
            Directory to unpack raw files into
        **kwargs:
            Remaining keywords arguments are passed directly to DataSource.process().
            See that docstring for details.

        Remaining keywords arguments are passed to the DataSource's `process()` method
        '''
        dataset_list, _ = available_datasources(keys_only=False)
        if dataset_name not in dataset_list:
            raise Exception(f'Unknown Dataset: {dataset_name}')
        dsrc = DataSource.from_dict(dataset_list[dataset_name])
        dsrc.fetch(fetch_path=fetch_path, force=force)
        dsrc.unpack(unpack_path=unpack_path, force=force)
        ds = dsrc.process(cache_path=cache_path, force=force, **kwargs)

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

    def dump(self, file_base=None, dump_path=None, hash_type='sha1',
             force=True, create_dirs=True, dump_metadata=True):
        """Dump a dataset.

        Note, this dumps a separate copy of the metadata structure,
        so that metadata can be looked up without loading the entire dataset,
        which could be large

        dump_metadata: boolean
            If True, also dump a standalone copy of the metadata.
            Useful for checking metadata without reading
            in the (potentially large) dataset itself
        file_base: string
            Filename stem. By default, just the dataset name
        hash_type: {'sha1', 'md5'}
            Hash function to use for hashing data/labels
        dump_path: path. (default: `paths['processed_data_path']`)
            Directory where data will be dumped.
        force: boolean
            If False, raise an exception if the file already exists
            If True, overwrite any existing files
        create_dirs: boolean
            If True, `dump_path` will be created (if necessary)

        """
        if dump_path is None:
            dump_path = paths['processed_data_path']
        dump_path = pathlib.Path(dump_path)

        if file_base is None:
            file_base = self.name

        metadata = self['metadata']

        metadata_filename = file_base + '.metadata'
        dataset_filename = file_base + '.dataset'
        metadata_fq = dump_path / metadata_filename

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
            logger.debug(f'Wrote Dataset Metadata: {metadata_filename}')

        dataset_fq = dump_path / dataset_filename
        with open(dataset_fq, 'wb') as fo:
            joblib.dump(self, fo)
        logger.debug(f'Wrote Dataset: {dataset_filename}')


class DataSource(object):
    """Representation of a data source"""

    def __init__(self,
                 name='datasource',
                 parse_function=None,
                 dataset_dir=None,
                 file_list=None):
        """Create a DataSource
        Parameters
        ----------
        name: str
            name of dataset
        parse_function: func (or partial)
            Function that will be called to process raw data into usable Dataset
        dataset_dir: path
            default location for raw files
        file_list: list
            list of file_dicts associated with this DataSource.
            Valid keys for each file_dict include:
                url: (optional)
                    URL of resource to be fetched
                hash_type: {'sha1', 'md5', 'sha256'}
                    Type of hash function used to verify file integrity
                hash_value: string
                    Value of hash used to verify file integrity
                file_name: string (optional)
                    filename to use when saving file locally. If omitted, it will be inferred from url or source_file
                name: string or {'DESCR', 'LICENSE'} (optional)
                    description of the file. of DESCR or LICENSE, will be used as metadata
                unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
                    action to take in order to unpack this file. If None, infers from file type.

        """
        if file_list is None:
            file_list = []

        if dataset_dir is None:
            dataset_dir = paths['raw_data_path']
        if parse_function is None:
            parse_function = process_dataset_default
        self.name = name
        self.file_dict = {infer_filename(**item):item for item in file_list}
        self.parse_function = parse_function
        self.dataset_dir = dataset_dir

        # sklearn-style attributes. Usually these would be set in fit()
        self.fetched_ = False
        self.fetched_files_ = []
        self.unpacked_ = False
        self.unpack_path_ = None

    @property
    def file_list(self):
        """For backwards compatibility while replacing the file_list with a file_dict"""
        logger.warning("file_list is deprecated. Use file_dict instead")
        return list(self.file_dict.values())

    def add_metadata(self, filename=None, contents=None, metadata_path=None, kind='DESCR', unpack_action='copy', force=False):
        """Add metadata to a DataSource

        filename: create metadata entry from contents of this file
        contents: create metadata entry from this string
        metadata_path: (default `paths['raw_data_path']`)
            Where to store metadata
        kind: {'DESCR', 'LICENSE'}
        unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
            action to take in order to unpack this file. If None, infers from file type.
        force: boolean (default False)
            If True, overwrite an existing entry for this file
        """
        if metadata_path is None:
            metadata_path = paths['raw_data_path']
        else:
            metadata_path = pathlib.Path(metadata_path)
        filename_map = {
            'DESCR': f'{self.name}.readme',
            'LICENSE': f'{self.name}.license',
        }
        if kind not in filename_map:
            raise Exception(f'Unknown kind: {kind}. Must be one of {filename_map.keys()}')

        if filename is not None:
            filelist_entry = {
                'fetch_action': 'copy',
                'file_name': str(filename),
                'name': kind,
            }
        elif contents is not None:
            filelist_entry = {
                'contents': contents,
                'fetch_action': 'create',
                'file_name': filename_map[kind],
                'name': kind,
            }
        else:
            raise Exception(f'One of `filename` or `contents` is required')

        if unpack_action:
            filelist_entry.update({'unpack_action': unpack_action})

        fn = filelist_entry['file_name']
        if fn in self.file_dict and not force:
            raise Exception(f"{fn} already exists in file_dict. Set `force=True` to overwrite.")
        self.file_dict[fn] = filelist_entry
        self.fetched_ = False

    def add_manual_download(self, message=None, *,
                            hash_type='sha1', hash_value=None,
                            name=None, file_name=None, unpack_action=None,
                            force=False):
        """Add a manual download step to the file list.

        Some datasets must be downloaded manually (usually ones that
        require opting-in to a specific set of terms and conditions).
        This method displays a message indicating how the user can manually
        download the file, and from where.

        message: string
            Message to be displayed to the user. This message indicates
            how to download the indicated dataset.
        hash_type: {'sha1', 'md5', 'sha256'}
        hash_value: string. required
            Hash, computed via the algorithm specified in `hash_type`
        file_name: string, required
            Name of destination file. relative to paths['raw_data_dir']
        name: str
            text description of this file.
        force: boolean (default False)
            If True, overwrite an existing entry for this file
        unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
            action to take in order to unpack this file. If None, infers from file type.
        """
        if hash_value is None:
            raise Exception("You must specify a `hash_value` "
                            "for a manual download")
        if file_name is None:
            raise Exception("You must specify a file_name for a manual download")

        if file_name in self.file_dict and not force:
            raise Exception(f"{file_name} already in file_dict. Use `force=True` to overwrite")

        fetch_dict = {
            'fetch_action': 'message',
            'file_name': file_name,
            'hash_type': hash_type,
            'hash_value': hash_value,
            'message': message,
            'name': name,
        }
        if unpack_action:
            fetch_dict.update({'unpack_action': unpack_action})

        self.file_dict[file_name] = fetch_dict
        self.fetched_ = False


    def add_file(self, source_file=None, *, hash_type='sha1', hash_value=None,
                 name=None, file_name=None, unpack_action=None,
                 force=False):
        """
        Add a file to the file list.

        This file must exist on disk, as there is no method specified for fetching it.
        This is useful when the data source requires an offline procedure for downloading.

        hash_type: {'sha1', 'md5', 'sha256'}
        hash_value: string or None
            if None, hash will be computed from specified file
        file_name: string
            Name of destination file. relative to paths['raw_data_dir']
        name: str
            text description of this file.
        source_file: path
            file to be copied
        force: boolean (default False)
            If True, overwrite an existing entry for this file
        unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
            action to take in order to unpack this file. If None, infers from file type.
        """
        if source_file is None:
            raise Exception("`source_file` is required")
        source_file = pathlib.Path(source_file)

        if not source_file.exists():
            logger.warning(f"{source_file} not found on disk")

        file_name = infer_filename(file_name=file_name, source_file=source_file)

        if hash_value is None:
            logger.debug(f"Hash unspecified. Computing {hash_type} hash of {source_file.name}")
            hash_value = hash_file(source_file, algorithm=hash_type).hexdigest()

        fetch_dict = {
            'fetch_action': 'copy',
            'file_name': file_name,
            'hash_type': hash_type,
            'hash_value': hash_value,
            'name': name,
            'source_file': str(source_file),
        }
        if unpack_action:
            fetch_dict.update({'unpack_action': unpack_action})

        existing_files = [f['source_file'] for k,f in self.file_dict.items()]
        existing_hashes = [f['hash_value'] for k,f in self.file_dict.items() if f['hash_value']]
        if file_name in self.file_dict and not force:
            raise Exception(f"{file_name} already in file_dict. Use `force=True` to add anyway.")
        if str(source_file.name) in existing_files and not force:
            raise Exception(f"source file: {source_file} already in file list. Use `force=True` to add anyway.")
        if hash_value in existing_hashes and not force:
            raise Exception(f"file with hash {hash_value} already in file list. Use `force=True` to add anyway.")

        logger.warning("Reproducibility Issue: add_file is often not reproducible. If possible, use add_manual_download instead")
        self.file_dict[file_name] = fetch_dict
        self.fetched_ = False

    def add_url(self, url=None, *, hash_type='sha1', hash_value=None,
                name=None, file_name=None, force=False):
        """
        Add a URL to the file list

        hash_type: {'sha1', 'md5', 'sha256'}
        hash_value: string or None
            if None, hash will be computed from downloaded file
        file_name: string or None
            Name of downloaded file. If None, will be the last component of the URL
        url: string
            URL to fetch
        name: str
            text description of this file.
        force: boolean (default False)
            If True, overwrite an existing entry for this file
        unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
            action to take in order to unpack this file. If None, infers from file type.
        """
        if url is None:
            raise Exception("`url` is required")

        file_name = infer_filename(file_name=file_name, url=url)

        fetch_dict = {
            'fetch_action': 'url',
            'file_name': file_name,
            'hash_type': hash_type,
            'hash_value': hash_value,
            'name': name,
            'url': url,
        }
        if unpack_action:
            filelist_entry.update({'unpack_action': unpack_action})

        if file_name in self.file_dict and not force:
            raise Exception(f"{file_name} already in file_dict. Use `force=True` to add anyway.")
        self.file_dict[file_name] = fetch_dict
        self.fetched_ = False

    def dataset_opts(self, metadata=None, **kwargs):
        """Convert raw DataSource files into a Dataset constructor dict

        Parameters
        ----------
        metadata: dict or None
            If None, an empty metadata dictionary will be used.
        **kwargs: additional parameters to be passed to `extract_func`

        Returns
        -------
        Dictionary containing the following keys:
            dataset_name: (string)
                `dataset_name` that was passed to the function
            metadata: (dict)
                dict containing the input `metadata` key/value pairs, and (optionally)
                additional information about this raw dataset
            data: array-style object
                Often a `numpy.ndarray` or `pandas.DataFrame`
            target: (optional) vector-style object
                for supervised learning problems, the target vector associated with `data`
        """
        if metadata is None:
            metadata = {}

        data, target = None, None

        if self.parse_function is None:
            logger.warning("No `parse_function` defined. `data` and `target` will be None")
        else:
            data, target, metadata = self.parse_function(metadata=metadata, **kwargs)

        dset_opts = {
            'dataset_name': self.name,
            'metadata': metadata,
            'data': data,
            'target': target,
        }
        return dset_opts

    def fetch(self, fetch_path=None, force=False):
        """Fetch files in the `file_dict` to `raw_data_dir` and check hashes.

        Parameters
        ----------
        fetch_path: None or string
            By default, assumes dataset_dir

        force: Boolean
            If True, ignore the cache and re-download the fetch each time
        """
        if self.fetched_ and force is False:
            # validate the downloaded files:
            for filename, item in self.file_dict.items():
                raw_data_file = paths['raw_data_path'] / filename
                if not raw_data_file.exists():
                    logger.warning(f"{raw_data_file.name} missing. Invalidating fetch cache")
                    self.fetched_ = False
                    break
                raw_file_hash = hash_file(raw_data_file, algorithm=item['hash_type']).hexdigest()
                if raw_file_hash != item['hash_value']:
                    logger.warning(f"{raw_data_file.name} {item['hash_type']} hash invalid ({raw_file_hash} != {item['hash_value']}). Invalidating fetch cache.")
                    self.fetched_ = False
                    break
            else:
                logger.debug(f'Data Source {self.name} is already fetched. Skipping')
                return

        if fetch_path is None:
            fetch_path = self.dataset_dir
        else:
            fetch_path = pathlib.Path(fetch_path)

        self.fetched_ = False
        self.fetched_files_ = []
        for key, item in self.file_dict.items():
            status, result, hash_value = fetch_file(**item)
            logger.debug(f"Fetching {key}: status:{status}")
            if status:  # True (cached) or HTTP Code (successful download)
                item['hash_value'] = hash_value
                item['file_name'] = result.name
                self.fetched_files_.append(result)
            else:
                if item.get('fetch_action', False) != 'message':
                    logger.error(f"fetch of {key} returned: {result}")
                break
        else:
            self.fetched_ = True

        self.unpacked_ = False
        return self.fetched_

    def raw_file_list(self, return_hashes=False):
        """Returns the list of raw files.

        Parameters
        ----------
        return_hashes: Boolean
            If True, returns tuples (filename, hash_type, hash_value).
            If False (default), return filenames only

        Returns the list of raw files that will be present once data is successfully fetched"""
        if return_hashes:
            return [(key, item['hash_type'], item['hash_value']) \
                    for (key, item) in self.file_dict.items()]
        else:
            return [key for key in self.file_dict]

    def unpack(self, unpack_path=None, force=False):
        """Unpack fetched files to interim dir"""
        if not self.fetched_:
            logger.debug("unpack() called before fetch()")
            self.fetch()

        if self.unpacked_ and force is False:
            logger.debug(f'Data Source {self.name} is already unpacked. Skipping')
        else:
            if unpack_path is None:
                unpack_path = paths['interim_data_path'] / self.name
            else:
                unpack_path = pathlib.Path(unpack_path)
            for filename, item in self.file_dict.items():
                unpack(filename, dst_dir=unpack_path, unpack_action=item.get('unpack_action', None))
            self.unpacked_ = True
            self.unpack_path_ = unpack_path

        return self.unpack_path_

    def process(self,
                cache_path=None,
                force=False,
                return_X_y=False,
                use_docstring=False,
                **kwargs):
        """Turns the data source into a fully-processed Dataset object.

        This generated Dataset object is cached using joblib, so subsequent
        calls to process with the same file_list and kwargs should be fast.

        Parameters
        ----------
        cache_path: path
            Location of joblib cache.
        force: boolean
            If False, use a cached object (if available).
            If True, regenerate object from scratch.
        return_X_y: boolean
            if True, returns (data, target) instead of a `Dataset` object.
        use_docstring: boolean
            If True, the docstring of `self.parse_function` is used as the Dataset DESCR text.
        """
        if not self.unpacked_:
            logger.debug("process() called before unpack()")
            self.unpack()

        if cache_path is None:
            cache_path = paths['interim_data_path']
        else:
            cache_path = pathlib.Path(cache_path)

        # If any of these things change, recreate and cache a new Dataset

        meta_hash = self.to_hash(**kwargs)

        dset = None
        dset_opts = {}
        if force is False:
            try:
                dset = Dataset.load(meta_hash, data_path=cache_path)
                logger.debug(f"Found cached Dataset for {self.name}: {meta_hash}")
            except FileNotFoundError:
                logger.debug(f"No cached Dataset found. Re-creating {self.name}")

        if dset is None:
            metadata = self.default_metadata(use_docstring=use_docstring)
            supplied_metadata = kwargs.pop('metadata', {})
            dset_opts = self.dataset_opts(metadata={**metadata, **supplied_metadata}, **kwargs)
            dset = Dataset(**dset_opts)
            dset.dump(dump_path=cache_path, file_base=meta_hash)

        if return_X_y:
            return dset.data, dset.target

        return dset


    def default_metadata(self, use_docstring=False):
        """Returns default metadata derived from this DataSource

        This sets the dataset_name, and fills in `license` and `descr`
        fields if they are present, either on disk, or in the file list

        Parameters
        ----------
        use_docstring: boolean
            If True, the docstring of `self.parse_function` is used as the Dataset DESCR text.

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

        for key, fetch_dict in self.file_dict.items():
            name = fetch_dict.get('name', None)
            # if metadata is present in the URL list, use it
            if name in optmap:
                txtfile = get_dataset_filename(fetch_dict)
                with open(paths['raw_data_path'] / txtfile, 'r') as fr:
                    metadata[optmap[name]] = fr.read()
        if use_docstring:
            func = partial(self.parse_function)
            fqfunc, invocation =  partial_call_signature(func)
            metadata['descr'] =  f'Data processed by: {fqfunc}\n\n>>> ' + \
              f'{invocation}\n\n>>> help({func.func.__name__})\n\n' + \
              f'{func.func.__doc__}'

        metadata['dataset_name'] = self.name
        return metadata

    def to_hash(self, ignore=None, hash_type='sha1', **kwargs):
        """Compute a hash for this object.

        converts this object to a dict, and hashes the result,
        adding or removing keys as specified.

        hash_type: {'md5', 'sha1', 'sha256'}
            Hash algorithm to use
        ignore: list
            list of keys to ignore
        kwargs:
            key/value pairs to add before hashing
        """
        if ignore is None:
            ignore = ['dataset_dir']
        my_dict = {**self.to_dict(), **kwargs}
        for key in ignore:
            my_dict.pop(key, None)

        return joblib.hash(my_dict, hash_name=hash_type)

    def __hash__(self):
        return hash(self.to_hash())

    def to_dict(self):
        """Convert a DataSource to a serializable dictionary"""
        parse_function_dict = serialize_partial(self.parse_function)
        obj_dict = {
            'url_list': list(self.file_dict.values()),
            **parse_function_dict,
            'name': self.name,
            'dataset_dir': str(self.dataset_dir)
        }
        return obj_dict

    @classmethod
    def from_name(cls, datasource_name,
                  datasource_file='datasources.json',
                  datasource_path=None):
        """Create a DataSource from a dictionary key name.

        The `datasource_file` is a json file mapping datasource_name
        to its dictionary representation.

        Parameters
        ----------
        datasource_name: str
            Name of data source. Used as the key in the on-disk key_file
        key_file_path:
            Location of key_file (json dict containing data source defintion)
            if None, use source code module: src/data/{key_file_name}
        key_file_name:
            Name of json file containing key/dict map

        """
        datasources, _ = available_datasources(datasource_file=datasource_file,
                                                 datasource_path=datasource_path,
                                                 keys_only=False)
        return cls.from_dict(datasources[datasource_name])

    @classmethod
    def from_dict(cls, obj_dict):
        """Create a DataSource from a dictionary.

        name: str
            dataset name
        dataset_dir: path
            pathname to load and save dataset
        obj_dict: dict
            Should contain url_list, and parse_function_{name|module|args|kwargs} keys,
            name, and dataset_dir
        """
        file_list = obj_dict.get('url_list', [])
        parse_function = deserialize_partial(obj_dict)
        name = obj_dict['name']
        dataset_dir = obj_dict.get('dataset_dir', None)
        return cls(name=name,
                   parse_function=parse_function,
                   dataset_dir=dataset_dir,
                   file_list=file_list)
