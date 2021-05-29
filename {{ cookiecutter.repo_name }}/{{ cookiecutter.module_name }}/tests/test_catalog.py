import pytest
import pathlib

from src.data import Catalog
from src.log import logger

@pytest.fixture
def catalog(tmpdir):
    """Create a test catalog"""

    # Setup
    # tmpdir should be empty when we get here
    c = Catalog.create(catalog_path=tmpdir)
    yield c

    # Teardown

@pytest.fixture
def old_catalog_file():
    test_dir = pathlib.Path(__file__).parent.resolve()

    yield test_dir / 'data' / 'dataset-test.json'

def test_old_catalog_init(tmpdir, old_catalog_file):
    c = Catalog.from_old_catalog(old_catalog_file, catalog_path=tmpdir)
    # Verify the catalog is nonempty and contains the expected data
    assert len(c) == 4
    for dsname in ["wine_reviews_130k", "wine_reviews_150k", 'wine_reviews_130k_varietals_75', 'wine_reviews']:
        assert dsname in c

    # Should fail, as it already exists
    with pytest.raises(FileExistsError):
        c = Catalog.from_old_catalog(old_catalog_file, catalog_path=tmpdir)

    # Should succeed, as replace is set
    c = Catalog.from_old_catalog(old_catalog_file, catalog_path=tmpdir, replace=True)
