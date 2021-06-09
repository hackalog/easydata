import os
import pathlib as pl
import pytest
import shutil
import tempfile as tf

from src.log import logger


@pytest.fixture
def manage_config_ini(doctest_namespace):
    path_config_ini = pl.Path("config.ini")
    if path_config_ini.exists():
        # Save the current config.ini
        fd_temp, path_temp = tf.mkstemp()
        try:
            shutil.copyfile(path_config_ini, path_temp)
            path_config_ini.unlink()
            yield
            shutil.copyfile(path_temp, path_config_ini)
        finally:
            os.close(fd_temp)
            os.remove(path_temp)
    else:
        # Make sure we don't leave a spurious config.ini
        try:
            yield
        finally:
            if path_config_ini.exists():
                path_config_ini.unlink()
