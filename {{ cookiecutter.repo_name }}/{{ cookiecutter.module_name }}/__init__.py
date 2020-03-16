import pathlib
from ._paths import Paths

_module_dir = pathlib.Path(__file__).parent.resolve()

_path_defaults = {
    'data_path': '${project_path}/data',
    'raw_data_path': '${data_path}/raw',
    'interim_data_path': '${data_path}/interim',
    'processed_data_path': '${data_path}/processed',
    'project_path': '${catalog_path}/..',
}
_catalog_file = _module_dir.parent / "catalog" / "config.ini"

paths = Paths(_path_defaults, config_file=_catalog_file, config_section="Paths")
