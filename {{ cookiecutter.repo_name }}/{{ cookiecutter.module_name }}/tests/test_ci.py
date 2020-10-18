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
    def test_20_newsgroups(self):
        ds = Dataset.load('20_newsgroups')
        ds = Dataset.load('20_newsgroups')
        assert len(ds.data) == 18846
        assert len(ds.target) == 18846

def test_logging_is_debug_level():
    assert logger.getEffectiveLevel() == logging.DEBUG
