## Test dataset information
import logging
import unittest

from src.data import Dataset
from src import workflow
from src.log import logger
import src.log.debug


class TestDatasetsSmall(unittest.TestCase):
    """
    Basic smoke tests to ensure that the smaller (and more quickly processed)
    available datasets load and have some expected property.
    """
    def test_dataset(self)
        #ds = Dataset.load('dataset_name')
        assert True

def test_logging_is_debug_level():
    assert logger.getEffectiveLevel() == logging.DEBUG
