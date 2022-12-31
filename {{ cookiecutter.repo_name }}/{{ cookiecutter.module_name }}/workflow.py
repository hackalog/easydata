"""A module where we temporarily smooth our way around API issues in Easydata.

This is a place where we temporarily address UX and API issues in Easydata, usually by writing convenient wrappers around existing functionality.

Nothing in here is intended to be a stable API, so use at your own risk, as these contents are regularly deprecated.

"""

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
