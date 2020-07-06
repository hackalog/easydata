'''Methods for joining up parts of a Reproducible Data Science workflow

Data Sources
------------
Makefile target: `make process_sources` or `make sources`

This part of the process handles downloading, unpacking, and cacheing
raw data files, as well as assembling documentation and license
information. These files are located in `paths['raw_data_path']`.
Cache files and unpacked raw files are saved to `paths['interim_data_path']`.

The equivalent workflow command is `process_datasources()`.

Other relevant commands are:

XXX

Datasets
--------
Makefile target: `make transform_data` or `make data`

Datasets are one of two fundamental data types in a reproducible data
science flow.  Datasets may be transformed into new datasets, via functions called
"transformers". Transformed datasets are saved in `paths['processed_data_path']`

The equivalent workflow command to `make transform_data` is `apply_transforms()'
Other relevant commands are:

XXX
'''
from .data import (cached_datasets, dataset_catalog,
                   datasource_catalog, add_datasource, load_catalog, del_from_catalog,
                   process_datasources as make_sources)
from .data import (transformer_catalog, add_dataset,
                   apply_transforms as make_data)

__all__ = [
    'add_dataset',
    'add_datasource',
    'cached_datasets',
    'dataset_catalog',
    'datasource_catalog',
    'del_from_catalog',
    'load_catalog',
    'make_data',
    'make_sources',
    'transformer_catalog',
]
