from .decorators import SingletonDecorator
from .kvstore import KVStore
import pathlib

class PathStore(KVStore):
    """Persistent Key-Value store for project-level paths

    >>> b = PathStore(config_file='/tmp/project/catalog/config.ini', \
        project_path='${catalog_path}/..', \
        data_path='${project_path}/data', \
        persistent=False)

    By default, the project directory is the parent of the directory containing the `config_file`:

    >>> b['project_path']
    PosixPath('/tmp/project')
    >>> b['data_path']
    PosixPath('/tmp/project/data')

    The `catalog_path` is set upon instantiation and is read-only:

    >>> b['catalog_path']
    PosixPath('/tmp/project/catalog')
    >>> b['catalog_path'] = '/tmp'
    Traceback (most recent call last):
     ...
    AttributeError: catalog_path is write-protected

    Changing a value changes all values that expand to contain it:

    >>> b['project_path'] = '/tmp'
    >>> b['project_path']
    PosixPath('/tmp')
    >>> b['data_path']
    PosixPath('/tmp/data')

    We can have multiple levels of expansion:

    >>> b['raw_data_path'] = "${data_path}/raw"
    >>> b['raw_data_path']
    PosixPath('/tmp/data/raw')
    >>> b['project_path'] = '/tmp3'
    >>> b['data_path']
    PosixPath('/tmp3/data')
    >>> b['raw_data_path']
    PosixPath('/tmp3/data/raw')
    """

    # These keys should never be written to disk, though they may be used
    # as variables in relative paths
    _protected = ['catalog_path']

    def __init__(self, *args,
                 config_section='Paths', config_file=None,
                 **kwargs):
        """Handle the special case of the config file"""
        if config_file is None:
            self._config_file = "config.ini"
        else:
            self._config_file = pathlib.Path(config_file)
        super().__init__(*args, config_section=config_section, config_file=self._config_file, **kwargs)

    def _write(self):
        """temporarily hide protected keys when saving"""
        for key in self._protected:
            self._config.remove_option(self._config_section, key)
        super()._write()
        for key in self._protected:
            self._config.set(self._config_section, key, str(getattr(self, key)))

    def __setitem__(self, key, value):
        """Do not set a key if it is protected"""
        if key in self._protected:
            raise AttributeError(f"{key} is write-protected")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        """get keys (including protected ones), converting to paths and fully resolving them"""
        if key in self._protected:
            return getattr(self, key)
        return pathlib.Path(super().__getitem__(key)).resolve()

    @property
    def catalog_path(self):
        return self._config_file.parent.resolve()

@SingletonDecorator
class Paths(PathStore):
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
