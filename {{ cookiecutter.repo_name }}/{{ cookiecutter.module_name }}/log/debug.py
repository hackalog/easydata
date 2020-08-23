# Importing this module ensures that any logging going on is performed at the
# DEBUG level.

import logging
from {{ cookiecutter.module_name }}.log import logger

logger.setLevel(logging.DEBUG)
