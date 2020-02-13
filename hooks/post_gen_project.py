import pathlib
import shutil
import logging
import json
from cookiecutter.config import get_user_config

logger = logging.getLogger(__name__)

def copy_cookiecutter_resume(template_name='cookiecutter-easydata'):
    """Make a copy of the cookiecutter replay file in the generated project.

    By default, cookiecutter creates a replay directory in a user's ~/.cookiecutter
    directory. This hook copies that file to the generated project. This can't
    currently be used by cookiecutter, but it's nice to at least have this
    information saved for now.
    """

    config_obj = get_user_config()
    config_dir = pathlib.Path(config_obj['replay_dir'])

    src_path = config_dir / f'{template_name}.json'
    dst_path = f'{template_name}.json'  # relative to root of generated project

    logger.debug(f"Reading cookiecutter replay data from {src_path}")
    with open(src_path) as f:
        cookiecutter_opts = json.load(f)

    logger.info(f"Dumping cookiecutter replay info to {dst_path}")
    with open(dst_path, 'w') as fw:
        json.dump(cookiecutter_opts.get('cookiecutter', {}), fw, sort_keys=True, indent=4)

if __name__ == '__main__':
    copy_cookiecutter_resume()
