import json
import os
import pathlib
import sys
from functools import partial
from collections import Counter, defaultdict

import joblib
import fsspec
from sklearn.utils import Bunch
from sklearn.model_selection import train_test_split

from .. import paths
from ..log import logger
from ..utils import load_json, save_json, normalize_to_list
from .utils import partial_call_signature, serialize_partial, deserialize_partial, process_dataset_default
from .fetch import fetch_file,  get_dataset_filename, hash_file, unpack, infer_filename


__all__ = [
    'Dataset',
    'add_dataset',
    'dataset_catalog',
    'cached_datasets',
    'create_transformer_pipeline',
    'DataSource',
    'add_datasource',
    'datasource_catalog',
    'process_datasources',
    'TransformerGraph',
    'apply_transforms',
    'transformer_catalog',
    'dataset_from_datasource',
    'load_catalog',
    'del_from_catalog',
]

def default_transformer(dsdict, **kwargs):
    """Placeholder for transformerdata processing function.

    This is the identity function.

    Returns
    -------
    dsdict: The input dsdict unmodified
    """
    transformer_name = kwargs.get('transformer_name', 'unknown-transformer')
    logger.error(f"'{transformer_name}()' function not found. Define it add it to the `user` namespace for correct behavior")
    return dsdict

def cached_datasets(dataset_path=None, keys_only=True):
    """Get the set of datasets currently cached to disk.

    Does not check whether the hashes of these cached datasets are valid / present in the catalog

    Parameters
    ----------
    dataset_path: path
        location of saved dataset files
    keys_only: Boolean
        if True, return a set of dataset names
        if False, return dictionary mapping dataset names to their stored metadata

    Returns
    -------
    if (keys_only is False):
        dictionary mapping cached dataset name to its metadata
    else (keys_only is True):
        set of cached dataset names
    """
    if dataset_path is None:
        dataset_path = paths['processed_data_path']
    else:
        dataset_path = pathlib.Path(dataset_path)

    ds_dict = {}
    for dsfile in dataset_path.glob("*.metadata"):
        ds_stem = str(dsfile.stem)
        ds_meta = Dataset.from_disk(ds_stem, data_path=dataset_path, metadata_only=True)
        ds_dict[ds_stem] = ds_meta

    if keys_only:
        return set(ds_dict.keys())
    return ds_dict

def load_catalog(catalog_path=None, catalog_file='catalog.json', include_filename=False, keys_only=False):
    """Get the set of available datasets from the catalog (nodes in the transformer graph).

    Parameters
    ----------
    include_filename: boolean
        if True, returns a tuple: (list, filename)
    keys_only: boolean
        if True, only keys will be returned.
        Cannot be used with include_filename=True, as this can lead to data deletion
    catalog_path: path. (default: paths['catalog_dir'])
        Location of `catalog_file`
    catalog_file: str, default 'catalog.json'
        Name of json file that contains the dataset metadata

    Returns
    -------
    If include_filename is True:
        A tuple: (catalog_dict, catalog_file_fq)
    else:
        catalog_dict
    """
    if keys_only and include_filename:
        raise Exception("include_filenames=True implies keys_only=False")

    if catalog_path is None:
        catalog_path = paths['catalog_path']
    else:
        catalog_path = pathlib.Path(catalog_path)

    catalog_file_fq = catalog_path / catalog_file

    if catalog_file_fq.exists():
        catalog_dict = load_json(catalog_file_fq)
    else:
        logger.warning(f"Catalog '{catalog_file}' does not exist.")
        catalog_dict = {}

    if include_filename:
        return catalog_dict, catalog_file_fq
    if keys_only:
        return list(catalog_dict.keys())
    return catalog_dict

dataset_catalog = partial(load_catalog, catalog_file='datasets.json')
datasource_catalog = partial(load_catalog, catalog_file='datasources.json')
transformer_catalog = partial(load_catalog, catalog_file='transformers.json')

def del_from_catalog(key, catalog_path=None, catalog_file=None):
    """Delete an entry from the catalog file

    key: str
        name of key to delete
    catalog_path:
        location of `catalog_file`
    catalog_file:
        filename of catalog

    """
    catalog_dict, catalog_file_fq = load_catalog(catalog_path=catalog_path,
                                                 catalog_file=catalog_file,
                                                 include_filename=True)
    del(catalog_dict[key])
    save_json(catalog_file_fq, catalog_file)

class Dataset(Bunch):
    def __init__(self,
                 dataset_name=None,
                 data=None,
                 target=None,
                 metadata=None,
                 update_hashes=True,
                 catalog_path=None,
                 catalog_file='datasets.json',
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
            Data about the object. Key fields include `license_txt`, `descr`, and `hashes`
        update_hashes: Boolean
            If True, recompute the data/target hashes in the Metadata
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
        #self['extra'] = Extra.from_dict(metadata.get('extra', None))
        data_hashes = self.get_data_hashes()

        if update_hashes:
            self['metadata'] = {**self['metadata'], **data_hashes}

    def update_catalog(self, catalog_path=None, catalog_file='datasets.json'):
        """Update the dataset catalog with my metadata

        Parameters
        ----------
        catalog_path: path or None
            Location of catalog file. default paths['catalog_path']
        catalog_file: str
            dataset catalog file. relative to `catalog_path`. Default 'datasets.json'
        """
        dataset_name = self["metadata"]["dataset_name"]
        catalog, catalog_file_fq = dataset_catalog(catalog_path=catalog_path, catalog_file=catalog_file, include_filename=True)
        catalog[dataset_name] = self['metadata']
        logger.debug(f"Updating dataset catalog with '{dataset_name}' metadata")
        save_json(catalog_file_fq, catalog)


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
        elif key in ['extra_base', 'extra_auth_kwargs']:
            if self.name not in paths._config.sections():
                paths._config.add_section(self.name)
            if key == 'extra_auth_kwargs':
                paths._config.set(self.name, key, json.dumps(value, sort_keys=True))
            else:
                paths._config.set(self.name, key, value)
            paths._write()
            logger.debug(f"Writing {key} to [{self.name}] in local_config")
        else:
            super().__setattr__(key, value)

    def __delattr__(self, key):
        if key.isupper():
            del self['metadata'][key.lower()]
        elif key == 'name':
            raise Exception("name is mandatory")
        elif key == 'extra_base':
            if paths._config.has_section(self.name) and paths._config.has_option(self.name, key):
                paths._config.remove_option(self.name, key)
                paths._write()
                logger.debug(f"Removing {key} from [{self.name}] in local_config")
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

    # note: won't work because of __setattr_ magic above
    #@name.setter
    #def name(self, val):
    #    self['metadata']['dataset_name'] = val

    @property
    def has_target(self):
        return self['target'] is not None

    def resolve_local_config(self, key, default=None, kind="string"):
        """Check for local data, first from the local data store, then from metadata. Finally, from the supplied default
        """
        if paths._config.has_section(self.name) and paths._config.has_option(self.name, key):
            logger.debug(f"Retrieving {key} from [{self.name}] in local_config")
            local_config = paths._config.get(self.name, key)
        else:
            local_config = self.metadata.get(key, None)
            if local_config:
                logger.debug(f"Retrieving {key} from metadata")
            else:
                local_config = default
        if kind == "string":
            return str(local_config)
        elif kind == "json":
            return json.loads(local_config)
        else:
            raise Exception(f"Unknown kind: {kind}")

    @property
    def extra_base(self):
        return self.resolve_local_config("extra_base", paths['processed_data_path'] / f"{self.name}.extra")

    @property
    def extra_auth_kwargs(self):
        return self.resolve_local_config("extra_auth_kwargs", "{}", kind="json")

    # Note: won't work because of set/setattr magic above
    #@extra_base.deleter
    #def extra_base(self):
    #    if paths._config.has_section(self.name) and paths._config.has_option(self.name, "extra_base"):
    #        paths._config.remove_option("extra_base")


    # Note: Won't work because of setattr magic above
    #@extra_base.setter
    #def extra_base(self, val):
    #    if self.name not in paths._config.sections():
    #        paths._config.add_section(self.name)
    #    paths._config.set(self.name, "extra_base", val)
    #    paths._write()
    #    logger.debug(f"Writing {paths._config_file}")


    @classmethod
    def from_disk(cls, dataset_name, data_path=None, metadata_only=False, errors=True,
                  catalog_path=None, dataset_cache='datasets.json'):
        """Load a dataset by name (or its metadata)

        errors: Boolean
            if True, raise exception if dataset is not available on disk
            if False, returns None if not found
        metadata_only: Boolean
            if True, return only metadata. Otherwise, return the entire dataset
        dataset_name: str
            name of dataset_dir
        data_path: str
            path containing `dataset_name`
        catalog_path: str or None:
            path to data catalog. default paths['catalog_path']
        dataset_cache: str. default 'datasets.json'
            name of dataset cache file. Relative to `catalog_path`.
        """
        if catalog_path is None:
            catalog_path = paths['catalog_path']
        else:
            catalog_path = pathlib.Path(catalog_path)

        if data_path is None:
            data_path = paths['processed_data_path']
        else:
            data_path = pathlib.Path(data_path)

        metadata_fq = data_path / f'{dataset_name}.metadata'
        dataset_fq = data_path / f'{dataset_name}.dataset'
        dataset_cache_fq = catalog_path / dataset_cache

        if not metadata_fq.exists() and not dataset_fq.exists():
            if errors:
                raise FileNotFoundError(f"No dataset {dataset_name} in {data_path}.")
            else:
                return None
        with open(metadata_fq, 'rb') as fd:
            meta = joblib.load(fd)

        if metadata_only:
            return meta

        logger.debug(f"Load {dataset_name} from disk...")
        with open(dataset_fq, 'rb') as fd:
            ds = joblib.load(fd)
        return ds

    @classmethod
    def load(cls, dataset_name,
         metadata_only=False,
         dataset_cache_path=None,
         catalog_path=None,
         dataset_file='datasets.json',
         transformer_file='transformers.json',
        ):
        """
        Load a dataset (or its metadata) from the dataset catalog.

        The named dataset must exist in the `dataset_file`.

        If a cached copy of the dataset is present on disk, (and its hashes match those in the dataset catalog),
        the cached copy will be returned. Otherwise, the dataset will be regenerated by traversing the
        transformer graph.

        Parameters
        ----------
        dataset_name: str
            name of dataset in the `dataset_file`
        metadata_only: Boolean
            if True, return only metadata. Otherwise, return the entire dataset
        dataset_cache_path: str
            path containing cachec copy of `dataset_name`.
            Default `paths['processed_data_path']`
        catalog_path: str or None:
            path to data catalog (containing dataset_file and transformer_file)
            Default `paths['catalog_path']`
        dataset_file: str. default 'datasets.json'
            name of dataset catalog file. Relative to `catalog_path`.
        transformer_file: str. default 'transformers.json'
            name of dataset cache file. Relative to `catalog_path`.
        """
        if dataset_cache_path is None:
            dataset_cache_path = paths['processed_data_path']
        else:
            dataset_cache_path = pathlib.Path(dataset_cache_path)

        xform_graph = TransformerGraph(catalog_path=catalog_path,
                                       transformer_file=transformer_file,
                                       dataset_file=dataset_file)
        if dataset_name not in xform_graph.datasets:
            raise AttributeError(f"'{dataset_name}' not found in dataset catalog.")
        meta = xform_graph.datasets[dataset_name]
        catalog_hashes = meta.get('hashes')

        if metadata_only:
            return meta
        try:
            ds = cls.from_disk(dataset_name, data_path=dataset_cache_path,
                               metadata_only=metadata_only,
                               errors=True,
                               catalog_path=catalog_path,
                               dataset_cache=dataset_cache_path)
            logger.debug(f"Loaded {dataset_name} from disk.")
            generated_hashes = ds.metadata['hashes']
            if catalog_hashes is not None:
                if not ds.verify_hashes(catalog_hashes):
                    msg = (f"Dataset '{dataset_name}' hashes {generated_hashes} do not match catalog: {catalog_hashes}")
                    logger.warning(msg)
                    raise Exception(msg)
        except:
            logger.debug(f"Falling back to loading {dataset_name} from catalog.")
            ds = cls.from_catalog(
                dataset_name,
                metadata_only=metadata_only,
                dataset_cache_path=dataset_cache_path,
                catalog_path=catalog_path,
                dataset_file=dataset_file,
                transformer_file=transformer_file
            )

        return ds

    @classmethod
    def from_catalog(cls, dataset_name,
         metadata_only=False,
         dataset_cache_path=None,
         catalog_path=None,
         dataset_file='datasets.json',
         transformer_file='transformers.json',
         force=False
        ):
        """Load a dataset (or its metadata) from the dataset catalog.

        The named dataset must exist in the `dataset_file`.


        Parameters
        ----------
        dataset_name: str
            name of dataset in the `dataset_file`
        metadata_only: Boolean
            if True, return only metadata. Otherwise, return the entire dataset
        dataset_cache_path: str
            path containing cachec copy of `dataset_name`.
            Default `paths['processed_data_path']`
        catalog_path: str or None:
            path to data catalog (containing dataset_file and transformer_file)
            Default `paths['catalog_path']`
        dataset_file: str. default 'datasets.json'
            name of dataset catalog file. Relative to `catalog_path`.
        transformer_file: str. default 'transformers.json'
            name of dataset cache file. Relative to `catalog_path`.
        force: Boolean
            if True, ignore any Dataset cache and always regenerate
        """
        if dataset_cache_path is None:
            dataset_cache_path = paths['processed_data_path']
        else:
            dataset_cache_path = pathlib.Path(dataset_cache_path)

        xform_graph = TransformerGraph(catalog_path=catalog_path,
                                       transformer_file=transformer_file,
                                       dataset_file=dataset_file)
        if dataset_name not in xform_graph.datasets:
            raise AttributeError(f"'{dataset_name}' not found in datset catalog.")
        meta = xform_graph.datasets[dataset_name]
        catalog_hashes = meta.get('hashes')
        ## XX check if cached copy of dataset is already on disk

        if metadata_only:
            return meta

        ds = xform_graph.generate(dataset_name, force=force)
        if ds is None:
            return None

        generated_hashes = ds.metadata['hashes']
        if catalog_hashes is not None:
            if not ds.verify_hashes(catalog_hashes):
                raise Exception(f"Dataset '{dataset_name}' hashes {generated_hashes} do not match catalog: {catalog_hashes}")

        return ds

    @classmethod
    def from_datasource(cls, datasource_name,
                        dataset_name=None,
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
        datasource_name: str
            Name of DataSource to load. see `datasource_catalog()` for the current list
        dataset_name: str
            Name of dataset to create. By default this will be `datasource_name`
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
        if cache_path is None:
            cache_path = paths['interim_data_path']
        else:
            cache_path = pathlib.Path(cache_path)
        dsrc_dict = datasource_catalog()
        if datasource_name not in dsrc_dict:
            raise Exception(f'Unknown Datasource={datasource_name} specified for datset={dataset_name}')
        dsrc = DataSource.from_dict(dsrc_dict[datasource_name])
        if not dsrc.fetch(fetch_path=fetch_path, force_download=force):
            logger.debug("Fetch failed. Aborting.")
            return None

        if dsrc.unpack(unpack_path=unpack_path, force_unpack=force) is None:
            logger.debug("Unpack failed. Aborting.")
            return None
        ds = dsrc.process(cache_path=cache_path, force=force, dataset_name=dataset_name, **kwargs)
        return ds

    def get_data_hashes(self, exclude_list=None, hash_type='sha1'):
        """Compute a the hash of data items

        exclude_list: list or None
            List of attributes to skip.
            if None, skips ['metadata']

        hash_type: {'sha1', 'md5'}
            Algorithm to use for hashing. Must be valid joblib hash type
        """
        if exclude_list is None:
            exclude_list = ['metadata']

        ret = {}
        hashes = {}
        for key, value in self.items():
            if key in exclude_list:
                continue
            data_hash = joblib.hash(value, hash_name=hash_type)
            hashes[key] = f"{hash_type}:{data_hash}"
        ret["hashes"] = hashes
        return ret

    def verify_hashes(self, hashdict):
        """Verify the supplied hash dictionary is a subset of my hash dictionary

        Hashes are a dict of attributes mapped to their hash value
        Hash values are strings f"{hash_type}:{hash_value}"; e.g.
        {
            'data': 'sha1:38f65f3b11da4851aaaccc19b1f0cf4d3806f83b',
            'target': 'sha1:38f65f3b11da4851aaaccc19b1f0cf4d3806f83b'
        }

        This test is order independent; e.g.
        >>> ds = Dataset("test")
        >>> hashlist = list(ds.metadata['hashes'].items())
        >>> reverse_hashdict = dict(list(reversed(hashlist)))
        >>> ds.verify_hashes(reverse_hashdict)
        True
        """
        return hashdict.items() <= self.metadata['hashes'].items()

    def verify_extra(self, extra_base=None, file_dict=None, return_filelists=False, hash_types=['size']):
        """
        Verify that all files listed in the metadata EXTRA dict are accessible and have good hashes.

        Returns boolean - True if all files are accessible and have good hashes - and optional
        file lists.

        Parameters
        ----------
        extra_base: path or None
           base for the EXTRA filenames.
           if passed as explicit parameter, this location will be used
           if omitted, the dataset `extra_base` will be read (which checks the local_config,
           or self.EXTRA_BASE, in that order)
        file_dict: sub-dict of extra dict
           if None, default to the whole extra dict
        return_filelists: boolean, default False
           if True, returns triple (good_hashes, bad_hashes, missing_files)
           else, returns Boolean (all files good)
        hash_types: sublist of ['size', 'md5', 'sha1']
           hash types to check against

        Returns
        -------
        True if all files are accessible and have good hashes. False otherwise.

        if return_filelists is True, also returns a triple:

        (good, bad, missing) where

        good: List
            files that are accessible and have valid hashes
        bad: List
            files that are accessible but who fail hash checks
        missing: List
            files that are inaccessible

        """
        if extra_base is None:
            extra_base = self.extra_base
        extra_base = pathlib.Path(extra_base)
        extra_dict = self.metadata.get('extra', None)
        if file_dict is None:
            file_dict = extra_dict
        else:
            if not (file_dict.keys() <= extra_dict.keys()):
                raise ValueError(f"file_dict must be a subset of the metadata['extra'] dict")
            else:
                for key in file_dict.keys():
                    if not (file_dict[key].items() <= extra_dict[key].items()):
                        raise ValueError(f"file_dict must be a subset of the metadata['extra'] dict")

        retval = False
        bad_hash = []
        good_hash = []
        missing = []

        if file_dict is None:
            retval = True
        else:
            for directory in file_dict.keys():
                for file, meta_hash_list in file_dict[directory].items():
                    path = extra_base / directory / file
                    rel_path = pathlib.Path(directory) / file
                    if path.exists():
                        disk_hash_list = []
                        for hash_type in hash_types:
                            disk_hash_list.append(hash_file(path, algorithm=hash_type))
                        if set(meta_hash_list) <= set(disk_hash_list):
                            good_hash.append(rel_path)
                        else:
                            bad_hash.append(rel_path)
                    else:
                        missing.append(rel_path)
            if len(bad_hash) == 0 and len(missing) == 0:
                retval = True
        if return_filelists:
            return retval, good_hash, bad_hash, missing
        else:
            return retval

    def subselect_extra(self, rel_files):
        """Convert a (relative) pathname to an EXTRA dict

        Suitable for passing to verify_extra()
        """
        extra_dict = defaultdict(dict)
        for rel_file_path in rel_files:
            rel_path = pathlib.Path(rel_file_path)
            try:
                hashlist = self.EXTRA[str(rel_path.parent)][rel_path.name]
            except KeyError:
                raise KeyError(f"Not in EXTRA: {rel_file_path}") from None
            extra_dict[str(rel_path.parent)][rel_path.name] = hashlist
        return dict(extra_dict)

    def extra_file(self, relative_path):
        """Convert a relative path (relative to extra_base) to a fully qualified location

        extra_base may be prefixed with optional protocol like `s3://` and
        is suitable for passing to fsspec.open_files()

        Parameters
        ----------
        relative_path: string or list
            Relative filepath. Will be appended to extra_base (and an intervening '/' added as needed)
            extra_base can be prefixed with a protocol like `s3://` to read from alternate filesystems.
            To read from multiple files you can pass a globstring or a list of paths, with the caveat
            that they must all have the same protocol.
        """
        extra_base = self.extra_base
        if extra_base.startswith("/"):
            fqpath =  str(pathlib.Path(extra_base) / relative_path)
        elif extra_base.endswith('/'):
            fqpath = f"{extra_base}{relative_path}"
        else:
            fqpath = f"{extra_base}/{relative_path}"
        return fqpath

    def open_extra(self, relative_path, auth_kwargs=None, **kwargs):
        """Given a path (relative to extra_base), return an fsspec.OpenFile object

        Parameters
        ----------
        relative_path: string or list
            Relative filepath. Will be appended to extra_base (and an intervening '/' added as needed)
            extra_base can be prefixed with a protocol like `s3://` to read from alternate filesystems.
            To read from multiple files you can pass a globstring or a list of paths, with the caveat
            that they must all have the same protocol.
        auth_kwargs: dict or None
            Dictionary of parameters to pass as kwargs to fsspec.OpenFile. This is where you can
            should specify authentication information (e.g. AWS keys)
        **kwargs: dict
            Other parameters to pass to fsspec.open_files() e.g.
            compression, protocol, encoding, host, port, username, password, etc. See `fsspec.open()`

        Examples
        --------
        >>> with ds.open_extra('2020-01-*.csv') as f:
        ...    df = pd.read_csv(f)   # doctest: +SKIP

        Returns
        -------
        An `OpenFiles` instance, which is a list of OpenFile objects that can
        be used as a single context
        """
        if auth_kwargs is None:
            auth_kwargs = self.extra_auth_kwargs
        if auth_kwargs:
            logger.debug(f"Passing authentication information via auth_kwargs")

        return fsspec.open(self.extra_file(relative_path), **auth_kwargs, **kwargs)

    def dump(self, file_base=None, dump_path=None, hash_type='sha1',
             force=False, create_dirs=True, dump_metadata=True, update_catalog=True,
             catalog_path=None, catalog_file='datasets.json'):
        """Dump a dataset to disk.

        Note, this dumps a separate copy of the metadata structure,
        so that metadata can be looked up without loading the entire dataset,
        which could be large. It also (optionally, but by default) adds this
        metadata to the dataset catalog.

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
        update_catalog: Boolean
            if True, new metadata will be written to catalog
        catalog_path: path or None
            Location of catalog file. default paths['catalog_path']
        catalog_file: str
            dataset catalog file. relative to `catalog_path`. Default 'datasets.json'

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

        if update_catalog:
            self.update_catalog(catalog_path=catalog_path, catalog_file=catalog_file)

        dataset_fq = dump_path / dataset_filename
        with open(dataset_fq, 'wb') as fo:
            joblib.dump(self, fo)
        logger.debug(f'Wrote Dataset: {dataset_filename}')

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
        datasources = datasource_catalog()

    for dataset_name in datasources:
        dsrc = DataSource.from_catalog(dataset_name)
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

    rawds_list, rds_file_fq = datasource_catalog(include_filename=True)
    rawds_list[rawds.name] = rawds.to_dict()
    save_json(rds_file_fq, rawds_list)

class DataSource(object):
    """Representation of a data source"""

    def __init__(self,
                 name='datasource',
                 process_function=None,
                 download_dir=None,
                 file_list=None):
        """Create a DataSource
        Parameters
        ----------
        name: str
            name of dataset
        process_function: func (or partial)
            Function that will be called to process raw data into usable Dataset
        download_dir: path (default None)
            default location for raw files either absolute or
            relative to paths['raw_data_path']. If None, will download to
            paths['raw_data_path']
        file_list: list
            list of file_dicts associated with this DataSource.
            Valid keys for each file_dict include:
                url: (optional)
                    URL of resource to be fetched
                hash_type: {'sha1', 'md5'}
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

        if process_function is None:
            process_function = process_dataset_default
        self.name = name
        self.file_dict = {infer_filename(**item):item for item in file_list}
        self.process_function = process_function
        self.download_dir = download_dir

        # sklearn-style attributes. Usually these would be set in fit()
        self.fetched_ = False
        self.fetched_files_ = []
        self.unpacked_ = False
        self.unpack_path_ = None

    @property
    def download_dir_fq(self):
        """
        Return the fq path to the download dir as download_dir is relative.
        """
        if self.download_dir is None:
            return paths['raw_data_path']
        else:
            download_path = pathlib.Path(self.download_dir)
            if download_path.is_absolute():
                return download_path
            else:
                return paths['raw_data_path'] / self.download_dir

    @property
    def file_list(self):
        """For backwards compatibility while replacing the file_list with a file_dict"""
        logger.warning("file_list is deprecated. Use file_dict instead")
        return list(self.file_dict.values())

    def add_metadata(self, filename=None, contents=None, metadata_path=None, kind='DESCR', unpack_action='copy', force=False):
        """Add metadata to a DataSource

        filename: create metadata entry from contents of this file. Relative to `metadata_path`
        contents: create metadata entry from this string
        metadata_path: (default `paths['raw_data_path']`)
            where to store metadata files
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
            filename = pathlib.Path(filename)
            try:
                fn = filename.relative_to(metadata_path)
            except ValueError:
                fn = filename
            filelist_entry = {
                'fetch_action': 'copy',
                'file_name': str(fn),
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
        hash_type: {'sha1', 'md5'}
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

        hash_type: {'sha1', 'md5'}
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
            hash_value = hash_file(source_file, algorithm=hash_type)

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
                name=None, file_name=None, force=False, unpack_action=None, url_options=None):
        """Add a file to the file list by URL.

        hash_type: {'sha1', 'md5'}
            hash function that produced `hash_value`. Default 'sha1'
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
        url_options: dict or None
            if `url` is specified, these options will be passed to the requests.request() call
            made when fetching.
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
            fetch_dict.update({'unpack_action': unpack_action})
        if url_options:
            fetch_dict.update({'url_options': url_options})

        if file_name in self.file_dict and not force:
            raise Exception(f"{file_name} already in file_dict. Use `force=True` to add anyway.")
        self.file_dict[file_name] = fetch_dict
        self.fetched_ = False


    def add_google_drive(self, file_id=None, *, hash_type='sha1', hash_value=None,
                         name=None, file_name=None, force=False, unpack_action=None):
        """Add a file to the file list by google drive file ID.

        hash_type: {'sha1', 'md5'}
            hash function that produced `hash_value`. Default 'sha1'
        hash_value: string or None
            if None, hash will be computed from downloaded file
        file_name: string or None
            Name of downloaded file. If None, will be the file_id
        file_id: string
            Google Drive file ID
        name: str
            text description of this file.
        force: boolean (default False)
            If True, overwrite an existing entry for this file
        unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
            action to take in order to unpack this file. If None, infers from file type.
        """
        if file_id is None:
            raise Exception("`file_id` is required")

        file_name = infer_filename(file_name=file_name, url=file_id)

        fetch_dict = {
            'fetch_action': 'google-drive',
            'file_name': file_name,
            'hash_type': hash_type,
            'hash_value': hash_value,
            'name': name,
            'url': file_id,
        }
        if unpack_action:
            fetch_dict.update({'unpack_action': unpack_action})

        if file_name in self.file_dict and not force:
            raise Exception(f"{file_name} already in file_dict. Use `force=True` to add anyway.")
        self.file_dict[file_name] = fetch_dict
        self.fetched_ = False

    def dataset_constructor_opts(self, dataset_name=None, metadata=None, **kwargs):
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
        if dataset_name is None:
            dataset_name = self.name
        data, target = None, None

        if self.process_function is None:
            logger.warning("No `process_function` defined. `data` and `target` will be None")
        else:
            data, target, metadata = self.process_function(metadata=metadata, **kwargs)

        dset_opts = {
            'dataset_name': dataset_name,
            'metadata': metadata,
            'data': data,
            'target': target,
        }
        return dset_opts

    def fetch(self, fetch_path=None, fetch_options=None, force_download=False):
        """Fetch files in the `file_dict` to `raw_data_dir` and check hashes.

        Parameters
        ----------
        fetch_path: None or string
            By default, assumes download_dir

        fetch_options: dict or None
            Options to pass to fetch_file

        force_download: Boolean
            If True, ignore the cache and re-download the fetch each time
        """
        if fetch_options is None:
            fetch_options = {}
        if self.fetched_ and force_download is False:
            # validate the downloaded files:
            for filename, item in self.file_dict.items():
                raw_data_file = paths['raw_data_path'] / filename
                if not raw_data_file.exists():
                    logger.warning(f"{raw_data_file.name} missing. Invalidating fetch cache")
                    self.fetched_ = False
                    break
                hash_type = item.get('hash_type', 'sha1')
                raw_file_hash = hash_file(raw_data_file, algorithm=hash_type)
                if raw_file_hash != item['hash_value']:
                    logger.warning(f"{raw_data_file.name} hash invalid ({raw_file_hash} != {item['hash_value']}). Invalidating fetch cache.")
                    self.fetched_ = False
                    break
            else:
                logger.debug(f'Data Source {self.name} is already fetched. Skipping')
                return True

        if fetch_path is None:
            fetch_path = self.download_dir_fq
        else:
            fetch_path = pathlib.Path(fetch_path)

        self.fetched_ = False
        self.fetched_files_ = []
        self.fetched_ = True
        for filename, fetch_params in self.file_dict.items():
            fetch_kwargs = {**fetch_params, **fetch_options, 'force':force_download, 'dst_dir':self.download_dir}
            status, result, hash_value = fetch_file(**fetch_kwargs)
            if status:  # True (cached) or HTTP Code (successful download)
                fetch_params['hash_value'] = hash_value

                # This breaks because file_name should be relative
                # to raw_data_path
                #fetch_params['file_name'] = result.name
                if fetch_params.get('file_name', None) is None:
                    fetch_params['file_name'] = result.name
                self.fetched_files_.append(result)
            else:
                if fetch_params.get('fetch_action', False) != 'message':
                    logger.error(f"fetch of {filename} returned: {result}")
                self.fetched_ = False

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
            return [(key, item.get('hash_type', 'sha1'), item['hash_value']) \
                    for (key, item) in self.file_dict.items()]
        else:
            return [key for key in self.file_dict]

    def unpack(self, unpack_path=None, force_unpack=False):
        """Unpack fetched files to interim dir"""
        if not self.fetched_:
            logger.debug("unpack() called before fetch()")
            if not self.fetch():
                logger.debug(f"Fetch failed. Aborting unpack")
                return None

        if self.unpacked_ and force_unpack is False:
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
            Location of dataset cache.
        force: boolean
            If False, raise an error if the generated dataset exists
            If True, overwrite any existing processed dataset
        return_X_y: boolean
            if True, returns (data, target) instead of a `Dataset` object.
        use_docstring: boolean
            If True, the docstring of `self.process_function` is used as the Dataset DESCR text.
        """
        if not self.unpacked_:
            logger.debug("process() called before unpack()")
            self.unpack()

        if cache_path is None:
            cache_path = paths['interim_data_path']
        else:
            cache_path = pathlib.Path(cache_path)

        # If any of these things change, recreate and cache a new Dataset

        meta_hash, hash_dict = self.to_hash(include_dict=True, **kwargs)

        dset = None
        dset_opts = {}

        if dset is None:
            metadata = self.default_metadata(use_docstring=use_docstring)
            supplied_metadata = kwargs.pop('metadata', {})
            dset_opts = self.dataset_constructor_opts(metadata={**metadata, **supplied_metadata}, **kwargs)
            dset = Dataset(**dset_opts)
            # if we were going to cache the dataset, we would dump it here; e.g.
            # logger.debug(f"Caching dataset as {dataset_hash}...")
            # dset.dump(dump_path=cache_path, file_base=dataset_hash, force=force)

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
            If True, the docstring of `self.process_function` is used as the Dataset DESCR text.

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
            func = partial(self.process_function)
            fqfunc, invocation =  partial_call_signature(func)
            metadata['descr'] =  f'Data processed by: {fqfunc}\n\n>>> ' + \
              f'{invocation}\n\n>>> help({func.func.__name__})\n\n' + \
              f'{func.func.__doc__}'

        metadata['dataset_name'] = self.name
        return metadata

    def to_hash(self, ignore=None, hash_type='sha1', include_dict=False, **kwargs):
        """Compute a hash for this object.

        converts this object to a dict, and hashes the result,
        adding or removing keys as specified.

        hash_type: {'md5', 'sha1'}
            Hash algorithm to use
        ignore: list
            list of keys to ignore
        kwargs:
            key/value pairs to add before hashing
        include_dict: boolean
            if True, also compute the dict the hash was computed over
            Useful for troubleshooting
        """
        if ignore is None:
            ignore = ['download_dir']
        my_dict = {**self.to_dict(), **kwargs}
        for key in ignore:
            my_dict.pop(key, None)

        if include_dict:
            return joblib.hash(my_dict, hash_name=hash_type), my_dict
        return joblib.hash(my_dict, hash_name=hash_type)

    def __hash__(self):
        return hash(self.to_hash())

    def to_dict(self):
        """Convert a DataSource to a serializable dictionary"""
        process_function_dict = serialize_partial(self.process_function)
        obj_dict = {
            'url_list': list(self.file_dict.values()),
            **process_function_dict,
            'name': self.name
        }
        if self.download_dir_fq != paths['raw_data_path']:
            obj_dict['download_dir'] = str(self.download_dir_fq)
        return obj_dict

    @classmethod
    def from_catalog(cls, datasource_name,
                  datasource_file='datasources.json',
                  datasource_path=None):
        """Create a DataSource from its JSON catalog name.

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
        datasources = datasource_catalog(catalog_file=datasource_file,
                                         catalog_path=datasource_path)
        return cls.from_dict(datasources[datasource_name])

    @classmethod
    def from_dict(cls, obj_dict, name=None):
        """Create a DataSource from a dictionary.

        name: str
            dataset name
        download_dir: path
            pathname to load and save dataset
        obj_dict: dict
            Should contain url_list, and load_function_{name|module|args|kwargs} keys,
            name, and download_dir
        name: str or None
            Name to be used for this dataset. If not specified, will be takedn from obj_dict
        """
        file_list = obj_dict.get('url_list', [])
        process_function = deserialize_partial(obj_dict, key_base='load_function')
        if name is None:
            name = obj_dict['name']
        download_dir = obj_dict.get('download_dir', None)
        return cls(name=name,
                   process_function=process_function,
                   download_dir=download_dir,
                   file_list=file_list)


class TransformerGraph:
    """Dataset Dependency Graph, consisting of Datasets and Transformers

    A "transformer" is a function that:

    * takes in zero or more `Dataset` objects (the `input_datasets`),
    * produces one or more `Dataset` objects (the `output_datasets`).

    Edges in this graph are directed, indicating the direction the direction of data dependencies.
    e.g. `output_datasets` depend on `input_datasets`.


    While the functions themselves are stores in the source module (default `src/user/transformers.py`),
    metadata describing these functions and which `Dataset` objects are generated are
    serialzed to `paths['catalog_path']/transformers.json`.

    Properties
    ----------
    nodes: set of dataset nodes (nodes in the hypergraph)
    edges: set of transformer nodes (edges in the hypergraph)
    """

    def __init__(self, catalog_path=None, transformer_file='transformers.json', dataset_file='datasets.json'):
        """Create the Transformer (Dataset Dependency) Graph

        This can be thought of as a bipartite graph (node sets are datasets and transformers respectively), or a hypergraph,
        (nodes=datasets, edges=transformers) depending on your preference.

        catalog_path:
            Location of catalog files. Default paths['catalog_path']
        transformer_file:
            Catalog file. default 'transformers.json'. Relative to catalog_path
        dataset_file:
            Default 'transformers.json'. Relative to `catalog_path`
        """
        if catalog_path is None:
            catalog_path = paths['catalog_path']
        else:
            catalog_path = pathlib.Path(catalog_path)

        self.transformers, self._transformer_catalog_fq = transformer_catalog(catalog_path=catalog_path, catalog_file=transformer_file, include_filename=True)
        self.datasets, self._dataset_catalog_fq = dataset_catalog(catalog_path=catalog_path, catalog_file=dataset_file, include_filename=True)

        self._validate_hypergraph()
        self._update_degrees()

    def _update_degrees(self):
        """Update the counts of in- and out-edges.

        used to compute sinks and sources
        """
        self.edges_out = Counter()
        self.edges_in = Counter()
        for n in self.nodes:
            self.edges_in[n] = 0
            self.edges_out[n] = 0
        for he_name, he in self.transformers.items():
            for node in he['output_datasets']:
                self.edges_in[node] += 1
            for node in he.get('input_datasets', []):
                self.edges_out[node] += 1
            else:
                if self.is_source(he_name):
                    self.edges_in[node] = 0

    def _validate_hypergraph(self):
        """Check the basic structure of the hypergraph is valid"""

        valid = True
        for node in self.nodes:
            if node not in self.datasets:
                logger.warning(f"Node '{node}' not found in Dataset catalog.")
                valid = False

        return valid

    @property
    def nodes(self):
        ret = set()
        for he in self.transformers.values():
            for node in he['output_datasets']:
                ret.add(node)
        return ret

    @property
    def edges(self):
        return set(self.transformers)

    @property
    def sources(self):
        return [n for (n, count) in self.edges_in.items() if count < 1]

    @property
    def sinks(self):
        return [n for (n, count) in self.edges_out.items() if count < 1]

    def add_source(self,
                   datasource_name=None,
                   datasource_opts=None,
                   edge_name=None,
                   output_dataset=None,
                   output_datasets=None,
                   transformer_pipeline=None,
                   write_catalog=True,
                   force=False,
    ):
        """Add a source node to the Transformer Graph.

        Due to a quirk in definition, source nodes are actually generated by source "edges".
        If `write_catalog` is specified, this edge will be added to the transformer catalog and
        empty dataset definitions will be added to the dataset catalog.

        Parameters
        ----------
        datasource_name: string, optional
            Name of a DataSource to use to generate the output
            Setting this option will create a source node in the dataset flow graph
            (or a sink node in the data dependency graph).
            Transformers of this type must specify at most one entry in `output_datasets`
        datasource_opts: dict, optional
            Options to use when generating a Dataset from this DataSource
        edge_name: string
            Name for this transformer instance (must be unique).
            By default, one will be created from the input and output dataset names; e.g.
            _input_ds1_input_ds2_to_output_ds1
        output_dataset: str
            Syntactic sugar for `output_datasets=(str)`
        output_datasets: iterable
            iterable containing list of output node names.
        transformer_pipeline: list
            list of serialized of transformer functions. (see `create_transformer_pipeline`)
            Function must be in the namespace of whatever attempts to deserialize it, or have a fully qualified
            module name.
        write_catalog: Boolean, Default True
            If False, don't actually write this entry to the catalogs.
        force: Boolean
            If True, overwrite entries in catalog
            If False, raise an exception on duplicate catalog entries

        Examples
        --------
        >>> dag = TransformerGraph(catalog_path='.')

        >>> dag.add_source(datasource_name='foo', write_catalog=False, force=True)
        {'_foo': {'transformations': [{'transformer_module': 'src.data.datasets', 'transformer_name': 'dataset_from_datasource', 'transformer_kwargs': {'dataset_name': 'foo', 'datasource_name': 'foo'}}], 'output_datasets': ['foo']}}


        How not to do it:

        >>> dag.add_source(datasource_opts={'foo':'bar'}, write_catalog=False)
        Traceback (most recent call last):
        ...
        Exception: `datasource_opts` requires a `datasource_name`

        >>> dag.add_source(output_dataset='bar', output_datasets=['foo', 'quux'], write_catalog=False)
        Traceback (most recent call last):
        ...
        Exception: Must specify at most one of `output_dataset` or `output_datasets`

        >>> dag.add_source(edge_name='foo', write_catalog=False)
        Traceback (most recent call last):
        ...
        Exception: At least one `output_dataset` or `datasource_name` is required

        Returns
        -------
        dict: {name: catalog_entry}
            where `catalog_entry` is the entry recorded in the transformer catalog
        """
        if datasource_opts and not datasource_name:
            raise Exception("`datasource_opts` requires a `datasource_name`")
        if output_dataset:
            if output_datasets:
                raise Exception("Must specify at most one of `output_dataset` or `output_datasets`")
            output_datasets = [output_dataset]
        if output_datasets is None:
            if datasource_name:
                output_datasets = [datasource_name]
            else:
                raise Exception("At least one `output_dataset` or `datasource_name` is required")
        if datasource_name and transformer_pipeline:
            raise Exception("Must specify either `datasource_name` or `transformer_pipeline`, not both")

        if datasource_name:  # special case. Convert this to a transformer call
            if not output_datasets:  # Default output_datasets
                output_datasets = [datasource_name]
            if datasource_opts is None:
                datasource_opts = {}
            datasource_transformer = partial(dataset_from_datasource, **datasource_opts,
                                             dataset_name=output_datasets[0],
                                             datasource_name=datasource_name)
            transformer_pipeline = create_transformer_pipeline([datasource_transformer])

        return self.add_edge(edge_name=edge_name,
                             force=force,
                             output_datasets=output_datasets,
                             transformer_pipeline=transformer_pipeline,
                             write_catalog=write_catalog)

    def add_edge(self,
                 input_dataset=None,
                 input_datasets=None,
                 edge_name=None,
                 output_dataset=None,
                 output_datasets=None,
                 transformer_pipeline=None,
                 write_catalog=True,
                 force=False,
    ):
        """Add an edge to the Transformer Graph.

        Edges involve zero or more input nodes (datasets) and
        one or more output nodes (datasets).

        Parameters
        ----------
        input_dataset: str
            Syntactic sugar for `input_datasets=(str)`
        input_datasets: iterable
            iterable containing list of input node names.
        edge_name: string
            Name for this transformer (edge) instance (must be unique).
            By default, one will be created from output dataset names; e.g.
            _output_ds1_output_ds2
        output_dataset: str
            Syntactic sugar for `output_datasets=(str)`
        output_datasets: iterable
            iterable containing list of output node names.
        transformer_pipeline: list
            list of serialized of transformer functions. (see `create_transformer_pipeline`)
            Function must be in the namespace of whatever attempts to deserialize it, or have a fully qualified
            module name.
        write_catalog: Boolean, Default True
            If False, don't actually write this entry to the catalogs.
        force: Boolean
            If True, overwrite entries in catalog
            If False, raise an exception on duplicate catalog entries

        Examples
        --------
        >>> dag = TransformerGraph(catalog_path='.')

        If you only have one input or output, it may be specified simply as a string;

        >>> dag.add_edge(input_dataset='other', output_dataset='p_other', write_catalog=False)
        {'_p_other': {'input_datasets': ['other'], 'output_datasets': ['p_other']}}
        >>> dag.add_edge(input_datasets=['other'], output_datasets=['p_other'], write_catalog=False)
        {'_p_other': {'input_datasets': ['other'], 'output_datasets': ['p_other']}}

        >>> dag.add_edge(input_datasets=['cc-by', 'cc-by-nc'], output_dataset='cc', write_catalog=False)
        {'_cc': {'input_datasets': ['cc-by', 'cc-by-nc'], 'output_datasets': ['cc']}}
        >>> dag.add_edge(input_datasets=['cc-by', 'cc-by-nc'], output_dataset='cc', write_catalog=False)
        {'_cc': {'input_datasets': ['cc-by', 'cc-by-nc'], 'output_datasets': ['cc']}}

        Names can be given explicitly:

        >>> dag.add_edge(input_datasets=['cc'], output_datasets=['cc_train','cc_test'], write_catalog=False)
        {'_cc_train_cc_test': {'input_datasets': ['cc'], 'output_datasets': ['cc_train', 'cc_test']}}
        >>> dag.add_edge(input_datasets=['cc'], output_datasets=['cc_train','cc_test'], edge_name='tts', write_catalog=False)
        {'tts': {'input_datasets': ['cc'], 'output_datasets': ['cc_train', 'cc_test']}}


        Invalid Use Cases:

        >>> dag.add_edge(output_dataset="foo", write_catalog=False)
        Traceback (most recent call last):
        ...
        Exception: Must specify either `input_datasets` or `transformer_pipeline`

        >>> dag.add_edge(input_dataset="foo", write_catalog=False)
        Traceback (most recent call last):
        ...
        Exception: At least one `output_dataset` is required


        Returns
        -------
        dict: {name: catalog_entry}
            where `catalog_entry` is the entry recorded in the transformer catalog
        """
        if output_dataset:
            if output_datasets:
                raise Exception("Must specify at most one of `output_dataset` or `output_datasets`")
            output_datasets = [output_dataset]
        if input_dataset:
            if input_datasets:
                raise Exception("Must specify at most one of `input_dataset` or `input_datasets`")
            input_datasets = [input_dataset]

        if output_datasets is None:
            raise Exception("At least one `output_dataset` is required")

        input_datasets = normalize_to_list(input_datasets)
        output_datasets = normalize_to_list(output_datasets)

        if edge_name is None:
            edge_name = f"_{'_'.join([ids for ids in output_datasets])}"

        if transformer_pipeline is None:
            if not input_datasets:
                raise Exception("Must specify either `input_datasets` or `transformer_pipeline`")
            transformer_pipeline = []

        catalog_entry = {}
        if input_datasets:
            catalog_entry['input_datasets'] = input_datasets
        if transformer_pipeline:
            catalog_entry['transformations'] = transformer_pipeline
        catalog_entry['output_datasets'] = output_datasets

        if edge_name in self.transformers and not force:
            raise Exception(f"Transformer '{edge_name}' already in catalog. Use force=True to overwrite")
        if write_catalog:
            self.transformers[edge_name] = catalog_entry
        for ds in set(output_datasets + input_datasets):
            if ds not in self.datasets:
                if write_catalog:
                    logger.info(f"Adding Dataset '{ds}' to catalog")
                    self.datasets[ds] = {'dataset_name': ds}
            else:
                if force:
                    logger.info(f"Updating Dataset '{ds}' in catalog")
                    self.datasets[ds] = {'dataset_name': ds}
                else:
                    logger.debug(f"Dataset '{ds}' already in catalog. Skipping")
        if write_catalog:
            logger.debug(f'Writing new catalog files')
            save_json(self._transformer_catalog_fq, self.transformers)
            save_json(self._dataset_catalog_fq, self.datasets)

        self._update_degrees()
        return {edge_name:catalog_entry}


    def find_child(self, node):
        """Find its parents, siblings and the edge that produced a given child node.
        Parameters
        ----------
        node: String
            name of an output node

        Returns
        -------
        (parents, edge, siblings) where

        parents: Set(str)
            parents needed to generate this child node
        edge: str
            name of the edge that generated this node
        siblings: Set(str)
            set of all the output nodes generated by this edge

        """
        for hename, he in self.transformers.items():
            if node in he['output_datasets']:
                return set(he.get('input_datasets', [])), hename, set(he['output_datasets'])
        raise KeyError(f"Node '{node}' not found in transformer graph")

    def is_source(self, edge):
        """Is this a source?

        Source edges terminate at a DataSource, and are identified
        by the an empty (or missing) input_datasets field
        """
        return not self.transformers[edge].get('input_datasets', False)

    def traverse(self, node, kind="breadth-first", force=False):
        """Find the path needed to regenerate the given node

        Traverse the graph as far as necessary to regenerate `node`.

        This will stop at the first upstream node whose parents are fully satisfied,
        (i.e. cached on disk, and whose hashes match the datset catalog)
        or all the way to source nodes, depending on the setting of `force`.

        Parameters
        ----------
        start: string
            Name of start node. Dendencies will be traced form this node back to sources

        kind: {'depth-first', 'breadth-first'}. Default 'breadth-first'
        force: Boolean
            if False, stop when all upstream dependencies are satisfied
            if True, always traverse all the way to source nodes.

        Returns
        -------
        (nodes , edges)
        where:
            nodes: List(str)
                list of node names traversed in the dependency graph
            edges: List(str)
                list of edge names traversed in the dependcy graph
        """
        if kind == 'breadth-first':
            pop_loc = 0
        elif kind == 'depth-first':
            pop_loc = -1
        else:
            raise Exception(f"Unknown kind: {kind}")
        visited = []
        edges = []
        queue = [node]
        while queue:
            vertex = queue.pop(pop_loc)
            if vertex not in visited:
                visited += [vertex]
                parents, edge, children = self.find_child(vertex)
                satisfied = self.fully_satisfied(edge)
                if satisfied:
                    if force:
                        logger.debug(f"All dependencies {parents} satisfied for edge: '{edge}' but force=True specified.")
                    else:
                        logger.debug(f"All dependencies {parents} satisfied for edge: '{edge}'")
                else:
                    logger.debug(f"Parent dependencies {parents} not satisfied for edge '{edge}'.")
                if not satisfied or force:
                    queue.extend(parents - set(visited))
                edges += [edge]
        return list(reversed(visited)), list(reversed(edges))

    def process_edge(self, edge_name, write_catalog=True, force=False, dataset_path=None):
        """Generate the outputs for a given edge

        This assumes all dependencies are on-disk and have valid caches.

        write_catalog: Boolean
            If True, and hashes match, write updated Dataset metadata into the catalog
        force: Boolean
            If True, write updated metadata even if Dataset hashes differ. Requires write_catalog=True
        dataset_path: path
            location of saved dataset files

        returns:
            dict {dataset_name: Dataset}
        """
        if force is True and write_catalog is False:
            raise Exception("Force=True requires write_catalog=True")

        if not self.fully_satisfied(edge_name):
            raise Exception(f"Edge '{edge_name}' has unsatisfied dependencies.")

        # All input datasets are on-disk and have valid caches

        edge = self.transformers[edge_name]
        dsdict = {}
        logger.debug(f"Processing input datasets for Edge '{edge_name}'")
        for in_ds in edge.get('input_datasets', []):  # sources have no inputs
            logger.debug(f"Loading Input Dataset '{in_ds}'")
            if in_ds not in self.datasets:
                raise Exception(f"Edge '{edge_name}' specifies an input dataset, '{in_ds}' that is not in the dataset catalog")
            ds = Dataset.from_disk(in_ds)
            if not self.check_dataset_hashes(in_ds, ds.HASHES):
                if force and write_catalog:
                    logger.debug(f"Dataset Hash mismatch for {in_ds} but force=True. Writing new hash to catalog")
                else:
                    raise Exception(f"Cached Dataset '{in_ds}' hashes {self.datasets[in_ds]['hashes']} do not match catalog {ds.HASHES}")
            dsdict[in_ds] = ds

        for xform_dict in edge.get('transformations', ()):
            transformer = deserialize_partial(xform_dict, key_base="transformer",
                                              fail_func=partial(default_transformer,
                                                                transformer_name=xform_dict['transformer_name']))
            logger.debug(f"Applying transformer: {xform_dict} to input datasets: {list(dsdict.keys())}")
            dsdict = transformer(dsdict)
            logger.debug(f"Obtained datasets: {list(dsdict.keys())}")
            cached_dsdicts = cached_datasets(dataset_path=dataset_path)
            success = True
            for ds_name, ds in dsdict.items():
                if ds is None:
                    logger.warning(f"Fetch failed for {ds_name}")
                    success = False
                    continue
                self.datasets[ds_name] = ds.metadata
                if write_catalog and (force or ds_name not in cached_dsdicts): # XXX and check hashes
                    logger.debug(f"Writing '{ds_name}' to processed data cache")
                    ds.dump(dump_path=dataset_path, force=force, update_catalog=False)
                logger.debug("Writing updated Dataset catalog")
                save_json(self._dataset_catalog_fq, self.datasets)
            if success is False:
                return None
        return dsdict


    def check_dataset_hashes(self, ds_name, hash_dict):
        """Verify that the supplied hash dictionary is a subset of the hashes in the Dataset catalog

        Parameters
        ----------
        ds_name: str
            name of a dataset in the Dataset catalog
        hash_dict: dict {str:str}
            Dict of attribute names and their associated hash values
            Hash values are strings f"{hash_type}:{hash_value}"; e.g. {
                'data': 'sha1:38f65f3b11da4851aaaccc19b1f0cf4d3806f83b',
                'target': 'sha1:38f65f3b11da4851aaaccc19b1f0cf4d3806f83b'
            }

        Returns
        -------
        True if all keys and values in hash_dict are present in (and equal to) the catalog entry for `ds_name`,
        or if no hashes are present in the Dataset catalog entry (i.e. the dataset has never been generated).
        False otherwise
        """
        if self.datasets[ds_name].get('hashes', None):
            cached_hashes, catalog_hashes = hash_dict, self.datasets[ds_name]['hashes']
            if not cached_hashes.items() <= catalog_hashes.items():
                logger.debug(f"Cached dataset '{ds_name}' hash {cached_hashes} != catalog hash {catalog_hashes}")
                return False
        return True

    def fully_satisfied(self, edge):
        """Determine whether all dependencies of the given edge (transformer) are satisfied

        Satisfied here means all input datasets are present (cached) on disk with valid hashes.
        Sources are always considered satisfied
        """
        if self.is_source(edge):
            return True

        input_datasets = self.transformers[edge].get('input_datasets', [])

        for ds_name in input_datasets:
            ds_meta = Dataset.from_disk(ds_name, metadata_only=True, errors=False)
            if not ds_meta:  # does not exist
                logger.debug(f"No cached dataset found for dataset '{ds_name}'.")
                return False
            if ds_name not in self.datasets:
                raise Exception(f"Missing '{ds_name}' in dataset catalog")
            if not self.check_dataset_hashes(ds_name, ds_meta['hashes']):
                return False


        return True

    def generate(self, dataset_name, write_catalog=True, force=False):
        """Generate the specified node (dataset)
        """
        _, edge_list = self.traverse(dataset_name)
        for edge in edge_list:
            dsdict = self.process_edge(edge, write_catalog=write_catalog, force=force)
            if dsdict is None:
                logger.error("Generation from catalog failed.")
                return None
        return dsdict.get(dataset_name, None)



def create_transformer_pipeline(func_list, ignore_module=False):
    """Create a serialize transformer pipeline.

    Output is suitable for passing to `TransformerGraph.add_{source|edge}`

    Parameters
    ----------
    func_list: iterable of callables
        Iterable containing functions (or partials) that should be serialized
    ignore_module: Boolean
        if True, remove the module from the serialized function call
        (i.e. rely on it being in the namespace when called)
        This makes it easy to eliminate some common errors when building
        transformer graphs in Notebooks

    Returns
    -------
    List of serialized function dictionaries (as per `serialize_partial`)
    """
    ret = []

    for f in func_list:
        serialized = serialize_partial(f, key_base='transformer')
        if ignore_module:
            del(serialized['transformer_module'])
        if not serialized['transformer_args']:
            del(serialized['transformer_args'])
        ret.append(serialized)

    return ret

def add_dataset(dataset=None, dataset_name=None, datasource_name=None, datasource_opts=None):
    """Add a Dataset to the dataset catalog

    dataset: Dataset
        Dataset object to add to catalog
    dataset_name:
        name to use when adding this object to the catalog

    datasource_name: str
        If specified, dataset will be generated from a datasource object with this name.
        Must be present in the datasource catalog
    datasource_opts: dict
        kwargs dictionary to use when generating this dataset

    """
    if dataset is not None and dataset_name is not None:
        raise Exception('Cannot use `dataset_name` if passing a `dataset` directly')

    if (dataset is None and datasource_name is None) or (dataset is not None and datasource_name is not None):

        raise Exception('Must specify exactly one of `dataset` or `datasource_name`')
    if datasource_name is not None:
        if dataset_name is None:
            dataset_name = datasource_name
        dataset = Dataset.from_datasource(datasource_name=datasource_name, dataset_name=dataset_name, **datasource_opts)

    catalog, catalog_fq = dataset_catalog(include_filename=True)
    catalog[dataset_name] = dataset.metadata
    save_json(catalog_fq, catalog)


def dataset_from_datasource(dsdict, *, datasource_name, dataset_name=None, **dsrc_args):
    """Transformer: Create a Dataset from a DataSource object

    This is just a thin wrapper around Dataset.from_datasource in order to
    conform to the transformer API

    Parameters
    ----------
    dsdict: dict, ignored.
        Because this is a source, this argument is unnecessary (except to
        conform to the transformer function API) and is ignored
    datasource_name: str, required
        Name of datasource in DataSource catalog
    dataset_name: str
        Name of the generated Dataset. If None, this will be the `datasource_name`
    dsrc_args: dict
        Arguments are the same as the `Dataset.from_datasource()` constructor

    Returns
    -------
    dict: {dataset_name: Dataset}
    """
    if dataset_name is None:
        dataset_name = datasource_name
    ds = Dataset.from_datasource(dataset_name=dataset_name, datasource_name=datasource_name, **dsrc_args)
    return {dataset_name: ds}

def transformer_catalog(
        catalog_path=None,
        catalog_file=None,
        include_filename=False,
    ):
    """Get the dictionary of transformers (edges in the transformer graph)

    Parameters
    ----------
    include_filename: boolean
        if True, returns a tuple: (list, filename)
    catalog_path: path. (default: paths['catalog_dir'])
        Location of `catalog_file`
    catalog_file: str, default 'transformers.json'
        Name of json file that contains the transformer pipeline

    Returns
    -------
    If include_filename is True:
        A tuple: (catalog_dict, catalog_file_fq)
    else:
        catalog_dict
    """
    if catalog_path is None:
        catalog_path = paths['catalog_path']
    else:
        catalog_path = pathlib.Path(catalog_path)
    if catalog_file is None:
        catalog_file = 'transformers.json'

    catalog_file_fq = catalog_path / catalog_file

    if catalog_file_fq.exists():
        catalog_dict = load_json(catalog_file_fq)
    else:
        logger.warning(f"Catalog '{catalog_file}' does not exist.")
        catalog_dict = {}

    if not isinstance(catalog_dict, dict):
        raise Exception(f"Obsolete file format: {transformer_file} must contain a dict.")

    if include_filename:
        return catalog_dict, catalog_file_fq
    return catalog_dict


def apply_transforms(datasets=None, transformer_path=None, transformer_file='transformer_list.json', output_dir=None):
    """Apply all data transforms to generate the specified datasets.

    transformer_file: string, default "transformer_list.json"
        Name of transformer file.
    transformer_path: path
        Path containing `transformer_file`. Default paths['catalog_path']
    output_dir: path
        Path to write the generated datasets. Default paths['processed_data_path']

    """

    if output_dir is None:
        output_dir = paths['processed_data_path']
    else:
        output_dir = pathlib.Path(output_dir)

    if transformer_path is None:
        transformer_path = paths['catalog_path']
    else:
        transformer_path = pathlib.Path(transformer_path)

    transformer_list = transformer_list(transformer_path=transformer_path,
                                            transformer_file=transformer_file)
    datasources = available_datasources()
    transformers = transformer_catalog()

    for tdict in transformer_list:
        datasource_opts = tdict.get('datasource_opts', {})
        datasource_name = tdict.get('datasource_name', None)
        output_dataset = tdict.get('output_dataset', None)
        input_dataset = tdict.get('input_dataset', None)
        transformations = tdict.get('transformations', [])
        if datasource_name is not None:
            if datasource_name not in datasources:
                raise Exception(f"Unknown DataSource: {datasource_name}")
            logger.debug(f"Creating Dataset from Raw: {datasource_name} with opts {datasource_opts}")
            rds = DataSource.from_catalog(datasource_name)
            ds = rds.process(**datasource_opts)
        else:
            logger.debug("Loading Dataset: {input_dataset}")
            ds = Dataset.from_disk(input_dataset)

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
