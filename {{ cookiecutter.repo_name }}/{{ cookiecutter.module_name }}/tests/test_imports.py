import unittest
import {{ cookiecutter.module_name }}.log.debug


class TestImports(unittest.TestCase):
    """
    Basic smoke test to ensure that the installed packages can actually be
    imported (we had a compatibility issue once that was not resolved
    properly by conda).
    """
    def test_infrastructure_packages(self):
        import gdown
        import sphinx
        import click
        import joblib
        import requests

    def test_common_packages(self):
        import numpy
        import scipy.sparse
        import pandas
        import bokeh
        import matplotlib
        import sklearn

    def test_extra_packages(self):
        import umap
        import umap.plot
