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
from .models.model_list import (get_model_list, add_model, del_model,
                                build_models as make_train,
                                available_models)

from .models.predict import (add_prediction, get_prediction_list,
                             pop_prediction,
                             run_predictions as make_predict,
                             available_predictions)
from .data import (Dataset, RawDataset, available_datasets, available_raw_datasets, add_raw_dataset,
                   process_raw_datasets as make_raw)
from .data.transform_data import (get_transformer_list, add_transformer, del_transformer,
                                  apply_transforms as make_data)
from .analysis.analysis import (available_scorers, available_analyses, get_analysis_list,
                                run_analyses as make_summarize,
                                add_analysis)

__all__ = [
    'add_analysis',
    'add_model',
    'add_prediction',
    'add_raw_dataset',
    'add_transformer',
    'available_algorithms',
    'available_analyses',
    'available_datasets',
    'available_models',
    'available_predictions',
    'available_raw_datasets',
    'available_scorers',
    'available_transformers',
    'del_model',
    'del_transformer',
    'get_analysis_list',
    'get_model_list',
    'get_prediction_list',
    'get_transformer_list',
    'make_data',
    'make_predict',
    'make_raw',
    'make_summarize',
    'make_train',
    'pop_prediction',
]
