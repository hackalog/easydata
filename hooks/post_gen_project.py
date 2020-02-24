import pathlib
import shutil
import logging
import json
from ruamel_yaml import YAML

from cookiecutter.config import get_user_config

logger = logging.getLogger(__name__)

def copy_cookiecutter_resume(template_name='cookiecutter-easydata'):
    """Make a copy of the cookiecutter replay file in the generated project.

    By default, cookiecutter creates a replay directory in a user's ~/.cookiecutter
    directory. This hook creates a YAML version of those values in the generated project.
    This can be used to regenerate the project by doing a:
    >>> cookiecutter --config_file path/to/cookiecutter-easydata.yaml cookiecutter-easydata

    """

    config_obj = get_user_config()
    config_dir = pathlib.Path(config_obj['replay_dir'])

    src_path = config_dir / f'{template_name}.json'
    dst_path = f'{template_name}.yaml'  # relative to root of generated project

    logger.debug(f"Reading cookiecutter replay data from {src_path}")
    with open(src_path) as f:
        cookiecutter_opts = json.load(f)
        yaml_opts = {k:v for k,v in cookiecutter_opts['cookiecutter'].items() if not k.startswith('_')}
    yaml = YAML()
    yaml.default_flow_style=False
    yaml.width=4096
    yaml.indent(offset=4)
    logger.info(f"Dumping cookiecutter replay info to {dst_path}")
    with open(dst_path, 'w') as fw:
        yaml.dump({'default_context': yaml_opts}, fw)


if __name__ == '__main__':
    copy_cookiecutter_resume()
