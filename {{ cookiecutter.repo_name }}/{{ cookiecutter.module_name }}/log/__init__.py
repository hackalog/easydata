import logging
import os
import sys

_log_fmt = '%(asctime)s - %(module)s - %(levelname)s - %(message)s'
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'), format=_log_fmt)
_MODULE = sys.modules[__name__]
logger = logging.getLogger(__name__)
