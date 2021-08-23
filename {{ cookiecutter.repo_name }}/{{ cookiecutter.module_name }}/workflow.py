# Workflow is where we patch around API issues in between releases.
# Nothing in this file is intended to be a stable API. use at your own risk,
# as its contents will be regularly deprecated
import sys
import logging
from .data import Catalog, Dataset, DataSource
from .log import logger

__all__ = [
    'make_target'
]

def make_target(target):
    """process command from makefile

    Parameters
    ----------
    target: target to execute
    """

    if target == "datasets":
        c = Catalog.load('datasets')
        for dsname in c:
            logger.info(f"Generating Dataset:'{dsname}'")
            ds = Dataset.load(dsname)
    elif target == "datasources":
        c = Catalog.load('datasources')
        for name in c:
            logger.info(f"Fetching, unpacking, and processing DataSource:'{name}'")
            dsrc = DataSource.from_catalog(name)
            ds = dsrc.process()
    else:
        raise NotImplementedError(f"Target: '{target}' not implemented")


if __name__ == '__main__':
    make_target(sys.argv[1])
