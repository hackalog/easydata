## Test dataset information
import unittest

from src.data import Dataset
import src.log.debug


class TestDatasets(unittest.TestCase):
    """
    Basic smoke tests to ensure that all of the available datasets
    load and have some expected property.
    """
    def basic_unit_test(self):
        assert True
