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
                 license_txt=None, descr_txt=None,
                 **kwargs):
        """
        use_dataset_list:
            if a `dataset_name` is specified,

        """
        super().__init__(**kwargs)

        if dataset_name is None:
            raise Exception('dataset_name is required')

        if metadata is not None:
            self['metadata'] = metadata
            use_cached_metadata = False
        else:
            self['metadata'] = {}
        self['metadata']['dataset_name'] = dataset_name
        self.LICENSE = license_txt
        self.DESCR = descr_txt
        self['data'] = data
        self['target'] = target

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
