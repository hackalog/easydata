import json
import os
import pathlib
import shutil

from collections.abc import MutableMapping
from ..log import logger
from ..utils import load_json, save_json
from .. import paths


__all__ = [
    'Catalog',
]


class Catalog(MutableMapping):
    """A catalog is a serializable, disk-backed git-friendly dict-like object for storing a data catalog.

    * "serializable" means anything stored in the catalog must be serializable to/from JSON.
    * "disk-backed" means all changes are reflected immediately in the on-disk serialization.
    * "git-friendly" means this on-disk format can be easily maintained in a git repo (with minimal
     issues around merge conflicts), and
    * "dict-like" means programmatically, it acts like a Python `dict`.

    On disk, a Catalog is stored as a directory of JSON files, one file per object
    The stem of the filename (e.g. stem.json) is the key (name) of the catalog entry
    in the dictionary, so `catalog/key.json` is accessible via catalog['key'].
    """

    def __init__(self,
                 catalog_name,
                 data=None,
                 catalog_path=None,
                 create=True,
                 delete=False,
                 extension="json",
                 ignore_errors=False,
                 merge_priority="data",
                 ):
        """
        catalog_name: str
            Name of the catalog. Also name of directory containing JSON catalog files. relative to `catalog_path`
        catalog_path: path. (default: paths['catalog_dir'])
            Location of catalog directory (i.e. data catalog is stored at `catalog_path/catalog_name`)
        create: Boolean
            if True, create the catalog if needed
        data:
            Dict-like object containing data to be merged into the catalog
        delete: boolean
            If catalog exists on disk, delete it before continuing
        extension: string
            file extension to use for serialized JSON files.
        ignore_errors: Boolean
            If True, errors in delete/create will be ignored
        merge_priority: {"disk", "data"}
            If using `data` with an existing repo, this indicates how to merge the two
            If disk, values already stored in the catalog will be retained
            If data, contents of `data` will override existing items on disk.

        """
        if catalog_path is None:
            self.catalog_path = paths['catalog_path']
        else:
            self.catalog_path = pathlib.Path(catalog_path)

        self.name = catalog_name
        self.extension = extension

        if data is None:
            data = {}

        if self.catalog_dir_fq.exists():  # Catalog exists on disk
            if delete:
                logger.debug(f"Deleting existing catalog dir: {self.name}")
                shutil.rmtree(self.catalog_dir_fq, ignore_errors=ignore_errors)

        # Load existing data (if it exists)
        self.data = {}
        disk_data = self._load(return_dict=True)
        logger.debug(f"Loaded {len(disk_data)} records from '{self.name}' Catalog.")

        if create:
            if not self.catalog_dir_fq.exists():  # Catalog exists on disk
                logger.debug(f"Creating new catalog:{self.name}")
                os.makedirs(self.catalog_dir_fq, exist_ok=ignore_errors)

        if data:
            logger.debug(f"Merging {len(disk_data)} on-disk and {len(data)} off-disk parameters")
            if merge_priority == "disk":
                self.data = {**data, **disk_data}
            elif merge_priority == "data":
                self.data = {**disk_data, **data}
            else:
                raise ValueError(f"Unknown merge_priority:{merge_priority}")
        else:
            self.__setitem__ = self._memory_setitem
            self.data = disk_data
            self.__setitem__ = self._disk_setitem

        self._verify_save()

    @property
    def file_glob(self):
        """glob string that will match all key files in this catalog directory.
        """
        return f"*.{self.extension}"

    @property
    def catalog_dir_fq(self):
        """pathlib.Path returning fully qualified path to catalog directory.
        """
        return self.catalog_path / self.name

    def __getitem__(self, key):
        return self.data[key]

    def _disk_setitem(self, key, value):
        self.data[key] = value
        self._save_item(key)

    def _memory_setitem(self, key, value):
        self.data[key] = value

    # So we can swap between behaviors
    __setitem__ = _disk_setitem

    def __delitem__(self, key):
        del self.data[key]
        self._del_item(key)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"<Catalog:{list(self.data.keys())}>"

    def __eq__(self, other):
        """Two catalogs are equal if they have the same contents,
        regardless of where or how they are stored on-disk.
        """
        return self.data == other.data

    def _load(self, return_dict=False):
        """reload an entire catalog from its on-disk serialization.

        if return_dict is True, return the data that would have been loaded,
        but do not change the contents of the catalog.

        """
        catalog_dict = {}
        logger.debug(f"Scanning on-disk catalog:'{self.name}'")
        for catalog_file in self.catalog_dir_fq.glob(self.file_glob):
            catalog_dict[catalog_file.stem] = load_json(catalog_file)

        if return_dict is True:
            return catalog_dict
        self.__setitem__ = self._memory_setitem
        self.data = catalog_dict
        self.__setitem__ = self._disk_setitem
        logger.debug(f"{len(self.data)} records loaded.")

    def _del_item(self, key):
        """Delete the on-disk serialization of a catalog entry"""
        filename = self.catalog_dir_fq / f"{key}.{self.extension}"
        logger.debug(f"Deleting catalog entry: '{key}.{self.extension}'")
        filename.unlink()

    def _save_item(self, key):
        """serialize a catalog entry to disk"""
        value = self.data[key]
        logger.debug(f"Writing entry:'{key}' to catalog:'{self.name}'.")
        save_json(self.catalog_dir_fq / f"{key}.{self.extension}", value)

    def _save(self, paranoid=True):
        """Save all catalog entries to disk

        if paranoid=True, verify serialization is equal to in-memory copy
        """
        logger.debug(f"Saving {len(self.data)} records to catalog '{self.name}'")
        for key in self.data:
            self._save_item(key)
        if paranoid:
            _verify_save()

    def _verify_save(self):
        logger.debug(f"Verifying serialization for catalog '{self.name}'")
        new = self._load(return_dict=True)
        if new != self.data:
            logger.error("Serialization failed. On-disk catalog differs from in-memory catalog")

    @classmethod
    def load(cls, name, create=True, ignore_errors=True, catalog_path=None):
        """Load a Catalog from disk.

        Parameters
        ----------
        name: String
            catalog name. Also the directory name for the serialized data
        create: Boolean
            If the catalog doesn't exist, create it.
        catalog_path:
            Path to where catalog will be created. Default: paths['catalog_path']
        ignore_errors: Boolean
            if False, and create=True, an error is thrown if the catalog already exists.
        """

        if catalog_path is None:
            catalog_path = paths['catalog_path']
        else:
            catalog_path = pathlib.Path(catalog_path)

        catalog_dir_fq = catalog_path / name
        if not catalog_dir_fq.exists() and not create:
            raise FileNotFoundError(f"Catalog:{name} not found and create=False")

        catalog = cls(name, create=create, ignore_errors=ignore_errors, catalog_path=catalog_path,
                      delete=False, data=None)
        return catalog

    @classmethod
    def create(cls, name, data=None, replace=False):
        """Create (or replace) a Catalog.

        Parameters
        ----------
        name: String
            catalog name. Also the directory name for the serialized data
        data: dict (or dict-like object)
            Initial contents of Catalog object
        replace: Boolean
            If True, replace an existing catalog.
            If False, an error is thrown if the catalog exists.
        """

        catalog = cls(name, create=True, delete=replace, data=data)
        return catalog


    @staticmethod
    def delete(name, ignore_errors=False, catalog_path=None):
        """Delete the on-disk Catalog

        Parameters
        ----------
        name: String
            Catalog name. Also the name of the directory to be deleted
        ignore_errors:
            If False, throw an error if catalog does not exist
        catalog_path:
            Directory containing catalog. Default paths['catalog_path']
        """
        if catalog_path is None:
            catalog_path = paths['catalog_path']
        else:
            catalog_path = pathlib.Path(catalog_path)

        logger.debug(f"Deleting existing catalog dir: {name}")
        shutil.rmtree(catalog_path / name, ignore_errors=ignore_errors)

    @classmethod
    def from_old_catalog(cls, catalog_file_fq, catalog_name=None, replace=False, catalog_path=None):
        """Create a catalog from an old combined-format JSON file

        Converts an old-format (combined) JSON catalog file to a new format (directory
        of JSON files) catalog file.

        Parameters
        ----------
        catalog_file_fq: String or Path
            fully qualified (or valid relative) path to old-format JSON catalog file
        catalog_name: None or String or Path
            if None, new-format catalog directory will be the stem (extensionless part)
            of `catalog_file_fq`
        replace: Boolean
            If True, an existing catalog file will be overwritten

        Other parameters are the same as per `Catalog.__init__()`
        """
        if catalog_path is None:
            catalog_path = paths['catalog_path']
        else:
            catalog_path = pathlib.Path(catalog_path)

        catalog_file_fq = pathlib.Path(catalog_file_fq)

        if catalog_file_fq.exists():
            catalog_dict = load_json(catalog_file_fq)
        else:
            logger.warning(f"Old catalog file:'{catalog_file_fq}' does not exist.")
            catalog_dict = {}

        if catalog_name is None:
            catalog_name = pathlib.Path(catalog_file_fq).stem

        catalog_dir_fq = catalog_path / catalog_name
        if catalog_dir_fq.exists() and not replace:
            raise FileExistsError(f"Catalog:{catalog_name} exists but replace=False")

        catalog = cls(catalog_name,
                      data=catalog_dict,
                      create=True, delete=replace,
                      catalog_path=catalog_path)
        return catalog
