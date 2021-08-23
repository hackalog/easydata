import pathlib
from ._paths import Paths

_module_dir = pathlib.Path(__file__).parent.resolve()

_path_defaults = {
    'cache_path': '${data_path}/interim/cache',
    'data_path': '${project_path}/data',
    'figures_path': '${output_path}/figures',
    'interim_data_path': '${data_path}/interim',
    'notebook_path': '${project_path}/notebooks',
    'output_path': '${project_path}/reports',
    'processed_data_path': '${data_path}/processed',
    'project_path': '${catalog_path}/..',
    'raw_data_path': '${data_path}/raw',
    'template_path': '${project_path}/reference/templates',
}
_catalog_file = _module_dir.parent / "catalog" / "config.ini"

paths = Paths(_path_defaults, config_file=_catalog_file, config_section="Paths")
