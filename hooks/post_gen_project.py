import pathlib
import shutil
import logging
import json
try:
    from ruamel_yaml import YAML
except ModuleNotFoundError:
    from ruamel.yaml import YAML

from cookiecutter.config import get_user_config

logger = logging.getLogger(__name__)


def copy_cookiecutter_resume(template_name='easydata'):
    """Make a copy of the cookiecutter replay file in the generated project.

    By default, cookiecutter creates a replay directory in a user's
    ~/.cookiecutter directory. This is largely useless. Easydata dumps
    this data to the generated project (also as json) using a jsonify
    call, but this doesn't yet help us regenerate the project
    automatically.  This hook creates a YAML version of those values
    in the generated project.  This can be used to regenerate the
    project by doing a:

    >>> cookiecutter --config_file path/to/.easydata.yaml easydata

    """
    # relative to root of generated project
    src_path = f'.{template_name}.json'
    yml_path = f'.{template_name}.yml'

    logger.debug(f"Reading cookiecutter replay data from {src_path}")
    with open(src_path) as f:
        cookiecutter_opts = json.load(f)
        yaml_opts = {k:v
                     for k,v in sorted(cookiecutter_opts.items())
                     if not k.startswith('_')}
    yaml = YAML()
    yaml.default_flow_style=False
    yaml.width=4096
    yaml.indent(offset=4)
    logger.debug(f"Dumping cookiecutter replay (YAML) info to {yml_path}")
    with open(yml_path, 'w') as fw:
        yaml.dump({'default_context': yaml_opts}, fw)

if __name__ == '__main__':
    copy_cookiecutter_resume()
