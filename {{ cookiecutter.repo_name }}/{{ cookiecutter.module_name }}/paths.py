import pathlib
import json
from .decorators import SingletonDecorator

# Get the project directory as the parent of this module location
src_module_dir = pathlib.Path(__file__).parent.resolve()
project_dir = src_module_dir.parent

data_path = project_dir / 'data'
catalog_path = project_dir / 'catalog'

raw_data_path = data_path / 'raw'
interim_data_path = data_path / 'interim'
processed_data_path = data_path / 'processed'

model_path = project_dir / 'models'
trained_model_path = model_path / 'trained'
model_output_path = model_path / 'outputs'

analysis_path = project_dir / 'reports'
summary_path = analysis_path / 'summary'
tables_path = analysis_path / 'tables'
figures_path = analysis_path / 'figures'

reports_path = project_dir / 'reports'

@SingletonDecorator
class Paths:
    """Dictionary-like object that exposes its keys as attributes with on-disk backing.

    >>> b = paths(project_dir='/tmp/project', src_module_dir='/tmp')
    >>> b.project_dir
    /tmp/project
    >>> b.src_module_dir
    /tmp
    >>> b.data_path
    /tmp/project/data
    >>> b.data_path='${src_module_dir}/data'
    >>> b.data_path
    /tmp/data
    """

    _defaults = {
        'project_dir': project_dir,
        'src_module_dir': src_module_dir,
        'data_path': project_dir / 'data',
        'catalog_path': project_dir / 'catalog',
        'raw_data_path': data_path / 'raw',
        'interim_data_path': data_path / 'interim',
        'processed_data_path': data_path / 'processed',
        'model_path': project_dir / 'models',
        'trained_model_path': model_path / 'trained',
        'model_output_path': model_path / 'outputs',
        'analysis_path': project_dir / 'reports',
        'summary_path': analysis_path / 'summary',
        'tables_path': analysis_path / 'tables',
        'figures_path': analysis_path / 'figures',
        'reports_path': project_dir / 'reports'
    }

    _dict = {}
    
    def __init__(self):
        paths_file = catalog_path / 'paths.json'
        if not paths_file.exists():
            self._dict = {k:str(v) for k,v in self._defaults.items()}
            self._write(paths_file)
        ondisk = self._read(paths_file)
        merged = {**self._defaults, **ondisk}
        self._dict = {k:str(v) for k,v in merged.items()}
        
    def __setattr__(self, key, value):
        if hasattr(self, key):
            super().__setattr__(key, value)
            return
        if key == 'catalog_path':
            raise AttributeError("catalog_path cannot be modified this way. Please edit `paths.py` instead")
        self._dict[key] = value
        paths_file = catalog_path / 'paths.json'
        self._write(paths_file)

    def __dir__(self):
        return self._dict.keys()

    def __repr__(self):
        return json.dumps(self._dict, sort_keys=True, indent=2)
    
    def __getattr__(self, key):
        try:
            return pathlib.Path(self._dict[key])
        except KeyError:
            raise AttributeError(key)

    def _write(self, filename):
        with open(filename, 'w') as fw:
            json.dump(dict(self._dict), fw, sort_keys=True, indent=2)

    def _read(self, filename):
        try:
            with open(filename, 'r') as fr:
                obj = json.load(fr)
        except FileNotFoundError:
            obj = {}
            self._write(filename)

        return obj
    def __iter__(self):
        for k in self._dict:
            yield(k)
