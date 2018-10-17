'''Methods for joining up parts of a Reproducible Data Science workflow

Raw Data:
---------
Makefile target: `make process_raw` or `make raw`

This part of the process handles downloading, unpacking, and cacheing
raw data files, as well as assembling documentation and license
information. These files are located in `paths.raw_data_path`.
Cache files and unpacked raw files are saved to `paths.interim_data_path`.

The equivalent workflow command is `process_raw_datasets()`.

Other relevant commands are:
     available_raw_datasets()
  `  add_raw_dataset()

Process Data:
-------------
Makefile target: `make transform_data` or `make data`

Datasets are one of two fundamental data types in a reproducible data
science flow.  Datasets may be transformed into new datasets, via functions called
"transformers". Transformed datasets are saved in `paths.processed_data_path`

The equivalent workflow command to `make transform_data` is `apply_transforms()'
Other relevant commands are:

    get_transformer_list()
    add_transformer()
    del_transformer()
    available_transformers()

Models: make train

Experiments: make predict

Analyses: make summary


'''
from .data.transformers import available_transformers
from .models import available_algorithms
from .models.model_list import (get_model_list, add_model, del_model, build_models,
                                available_models)

from .models.predict import (add_prediction, get_prediction_list,
                             pop_prediction, run_predictions, available_predictions)
from .data import (Dataset, RawDataset, available_datasets, available_raw_datasets, add_raw_dataset)
from .data.transform_data import get_transformer_list, add_transformer, del_transformer, apply_transforms
from .analysis.analysis import available_scorers, available_analyses, get_analysis_list, run_analyses, add_analysis

__all__ = [
    'available_datasets',
    'available_raw_datasets',
    'add_raw_dataset',
    'get_transformer_list',
    'apply_transforms',
    'add_transformer',
    'del_transformer',
    'available_transformers',
    'available_algorithms',
    'get_model_list',
    'add_model',
    'del_model',
    'available_models',
    'add_prediction',
    'get_prediction_list',
    'pop_prediction',
    'run_predictions',
    'available_predictions',
    'available_scorers',
    'available_analyses',
    'get_analysis_list',
    'run_analyses',
    'add_analysis',
]
