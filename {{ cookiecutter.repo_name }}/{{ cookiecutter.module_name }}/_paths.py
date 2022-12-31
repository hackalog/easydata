from .decorators import SingletonDecorator
from .kvstore import KVStore
from .log import logger
import pathlib import Path

class PathStore(KVStore):
    """Persistent Key-Value store for project-level paths

    >>> b = PathStore(config_file='/tmpx/project/catalog/config.ini', \
        project_path='${catalog_path}/..', \
        data_path='${project_path}/data', \
        persistent=False)

    By default, the project directory is the parent of the directory containing the `config_file`:


    >>> b['project_path'] == Path('/tmpx/project').resolve()
    True
    >>> b['data_path'] == Path('/tmpx/project/data').resolve()
    True

    The `catalog_path` is set upon instantiation and is read-only:

    >>> b['catalog_path'] == Path('/tmpx/project/catalog').resolve()
    True
    >>> b['catalog_path'] = '/tmp'
    Traceback (most recent call last):
     ...
    AttributeError: catalog_path is write-protected

    Changing a value changes all values that expand to contain it:

    >>> b['project_path'] = '/tmpy'
    >>> b['project_path'] ==  Path('/tmpy').resolve()
    True
    >>> b['data_path'] == Path('/tmpy/data').resolve()
    True

    We can have multiple levels of expansion:

    >>> b['raw_data_path'] = "${data_path}/raw"
    >>> b['raw_data_path'] == Path('/tmpy/data/raw').resolve()
    True
    >>> b['project_path'] = '/tmp3'
    >>> b['data_path'] == Path('/tmp3/data').resolve()
    True
    >>> b['raw_data_path'] == Path('/tmp3/data/raw').resolve()
    True
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
            self._config_file = Path(config_file)
        self._usage_warning = False
        super().__init__(*args, config_section=config_section,
                         config_file=self._config_file, **kwargs)
        self._usage_warning = True

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

        if self._usage_warning:
            logger.warning(f"'{key}' is a local configuration variable, and for reproducibility reasons, should not set from a notebook or shared code. It is better to edit '{self._config_file}' instead. We have set it, but you have been warned.")

        super().__setitem__(key, value)


    def __getitem__(self, key):
        """get keys (including protected ones), converting to paths and fully resolving them"""
        if key in self._protected:
            return getattr(self, key)
        self._read()
        return Path(super().__getitem__(key)).resolve()

    @property
    def catalog_path(self):
        return self._config_file.parent.resolve()

@SingletonDecorator
class Paths(PathStore):
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
