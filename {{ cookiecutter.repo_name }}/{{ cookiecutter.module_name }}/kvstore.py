import configparser
import pathlib
from collections.abc import MutableMapping

class KVStore(MutableMapping):
    """Dictionary-like key-value store backed to disk by a ConfigParser (ini) file

    Basic functionality is that of a dictionary, with the addition of an implicit
    `config_file` and `config_section`:

    >>> d = KVStore({'key1':'value1'}, key2='value2')
    >>> d['key3'] = 'value3'
    >>> d
    KVStore(config_file='config.ini', config_section='KVStore', key1='value1', key2='value2', key3='value3')


    To create a brand new, default KVStore, ignoring anything that may already be on disk:
    >>> d = KVStore(overwrite=True)
    >>> d
    KVStore(config_file='config.ini', config_section='KVStore', )

    KVStore values can reference other values via substitution using the
    `ConfigParser.ExtendedInterpolation` format. When the KVStore is viewed as a dict,
    this substitution happens automatically.

    >>> d = KVStore(root_path='/tmp', data_path='${root_path}/data')
    >>> dict(d)
    {'root_path': '/tmp', 'data_path': '/tmp/data'}
    >>> d['data_path']
    '/tmp/data'

    To see the unparsed (raw) value, examine the object's `data` method; e.g.
    >>> d.data
    {'root_path': '/tmp', 'data_path': '${root_path}/data'}

    This substitution is updated whenever a key changes; e.g.
    >>> d['raw_data_path'] = '${root_path}/raw'
    >>> d['root_path'] = '/tmp2'
    >>> dict(d)
    {'root_path': '/tmp2', 'data_path': '/tmp2/data', 'raw_data_path': '/tmp2/raw'}
    >>> d.data
    {'root_path': '/tmp2', 'data_path': '${root_path}/data', 'raw_data_path': '${root_path}/raw'}
    >>> d['data_path']
    '/tmp2/data'

    Because this object is disk-backed, newly instantiated objects will receive the last set of defaults:
    >>> c = KVStore()
    >>> dict(c)
    {'root_path': '/tmp2', 'data_path': '/tmp2/data', 'raw_data_path': '/tmp2/raw'}
    >>> c.data
    {'root_path': '/tmp2', 'data_path': '${root_path}/data', 'raw_data_path': '${root_path}/raw'}

    We can force overwriting of this disk-backed file using the `overwrite` parameters:
    >>> c = KVStore(overwrite=True)
    >>> dict(c), c.data
    ({}, {})
    """
    def __init__(self, *args,
                 config_file=None, config_section="KVStore", overwrite=False, persistent=True,
                 **kwargs):
        """Create a new disk-backed key-value store

        Arguments
        ---------
        config_file: Path
            path to ini (ConfigParser-formatted) file that will be used to persist the KVStore
        config_section: String
            Section name to be used in the `config_file`
        overwrite: Boolean
            If True, any config file on disk will be overwritten.
            Otherwise, existing values from this file will be used as defaults,
            (unless overridden by explicit key/value pairs in the constructor)
        *args, **kwargs:
            All other arguments will be used as per the standard `dict` constructor

        """
        self._persistent = persistent
        if config_file is None:
            self._config_file = pathlib.Path("config.ini")
        else:
            self._config_file = pathlib.Path(config_file)
        self._config_section = config_section
        self._config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())

        self.data = dict()

        if self._config_file.exists() and not overwrite:
            self._config.read(self._config_file)
            if not self._config.has_section(config_section):
                # File exists but we are adding to a new section of it
                self._config.add_section(config_section)
        else:
            self._config.add_section(config_section)
            self._config.read_dict(self.data)

        self.update({k:v for k,v in self._config.items(self._config_section, raw=True)}) # `update` comes for free from the abc
        self.update(dict(*args, **kwargs))
        self._write()

    def __getitem__(self, key):
        return self._config.get(self._config_section, key)

    def __setitem__(self, key, value):
        self.data[key] = value
        self._config.set(self._config_section, key, value)
        self._write()

    def __delitem__(self, key):
        del self.data[key]
        self._config.remove_option(self._config_section, key)
        self._write()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def _write(self):
        if self._persistent:
            with open(self._config_file, 'w') as fw:
                self._config.write(fw)

    def __repr__(self):
        kvstr = ", ".join([f"{k}='{v}'" for k,v in self.data.items()])
        return f"KVStore(config_file='{str(self._config_file)}', config_section='{self._config_section}', {kvstr})"

    def __str__(self):
        return str({k:v for k,v in self._config.items(self._config_section, raw=False)})

if __name__ == "__main__":
    import doctest
    doctest.testmod()
