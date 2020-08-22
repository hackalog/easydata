## Test dataset information
import logging
import unittest

from {{ cookiecutter.module_name }}.data import Dataset
from {{ cookiecutter.module_name }} import workflow
from {{ cookiecutter.module_name }}.log import logger
import {{ cookiecutter.module_name }}.log.debug


class TestDatasetsSmall(unittest.TestCase):
    """
    Basic smoke tests to ensure that the smaller (and more quickly processed)
    available datasets load and have some expected property.
    """
    def test_dataset(self):
        #ds = Dataset.load('dataset_name')
        assert True

def test_logging_is_debug_level():
    assert logger.getEffectiveLevel() == logging.DEBUG
