## To be run from inside a cookiecutter-easdata project conda environment
## that has the catalog files and structure of the test-env from the cookiecutter-easydata
## CI setup.

import subprocess
import tempfile
import unittest
from pathlib import Path
import requests

from src import paths

CCDS_ROOT = Path(__file__).parents[1].resolve()
DOCS_DIR = CCDS_ROOT / "docs"

def _exec_notebook(path):
    """
    Helper function to execute a notebook.
    """
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
        args = ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                "--ExecutePreprocessor.timeout=1000",
                "--ExecutePreprocessor.kernel_name=python",
                "--output", fout.name, path]
        subprocess.check_call(args)

class TestDocNotebooks(unittest.TestCase):
    """
    Test that the documentation notebooks run.
    """
    def test_notebook_00(self):
        _exec_notebook(DOCS_DIR / "00-xyz-sample-notebook.ipynb")

    def test_notebook_csv(self):
        csv_url = "https://storage.googleapis.com/covid19-open-data/v2/epidemiology.csv"
        csv_dest = paths['raw_data_path'] / "epidemiology.csv"
        if not csv_dest.exists():
            csv_file = requests.get(csv_url)
            with open(csv_dest, 'wb') as f:
                f.write(csv_file.content)
        _exec_notebook(DOCS_DIR / "Add-csv-template.ipynb")
