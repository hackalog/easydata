import joblib
import logging
import os
import pathlib
import sys
from sklearn.datasets.base import Bunch

from ..paths import raw_data_path, processed_data_path

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

__all__ = ['Dataset']

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
            super().__setattr__(name, value)

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

        if metadata_only:
            metadata_fq = data_path / f'{file_base}.metadata'
            with open(metadata_fq, 'rb') as fd:
                meta = joblib.load(fd)
            return meta

        with open(data_path / f'{file_base}.dataset', 'rb') as fd:
            ds = joblib.load(fd)
        return ds

    def dump(self, file_base=None, data_path=None, hash_type='sha1',
             force=True, create_dirs=True):
        """Dump a dataset.

        Note, this dumps a separate metadata structure, so that dataset
        metadata be read without reading in the (possibly large) data itself

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

        metadata['data_hash'] = joblib.hash(self.data, hash_name=hash_type)
        metadata['target_hash'] = joblib.hash(self.target, hash_name=hash_type)

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
        with open(metadata_fq, 'wb') as fo:
            joblib.dump(metadata, fo)
        logger.debug(f'Wrote metadata to {metadata_fq}')

        dataset_fq = data_path / dataset_filename
        with open(dataset_fq, 'wb') as fo:
            joblib.dump(self, fo)
        logger.debug(f'Wrote dataset to {dataset_fq}')
