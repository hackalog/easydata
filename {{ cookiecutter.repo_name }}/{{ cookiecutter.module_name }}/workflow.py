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
     available_datasources()
  `  add_datasource()

Process Data
------------
Makefile target: `make transform_data` or `make data`

Datasets are one of two fundamental data types in a reproducible data
science flow.  Datasets may be transformed into new datasets, via functions called
"transformers". Transformed datasets are saved in `paths['processed_data_path']`

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
from .data import (Dataset, DataSource, available_datasets,
                   available_datasources, add_datasource, del_datasource,
                   process_datasources as make_sources)
from .data.transform_data import (get_transformer_list, add_transformer, del_transformer,
                                  apply_transforms as make_data)
from .analysis.analysis import (available_scorers, available_analyses, get_analysis_list,
                                run_analyses as make_analysis,
                                add_analysis)

__all__ = [
    'add_analysis',
    'add_datasource',
    'add_model',
    'add_prediction',
    'add_transformer',
    'available_algorithms',
    'available_analyses',
    'available_datasets',
    'available_datasources',
    'available_models',
    'available_predictions',
    'available_scorers',
    'available_transformers',
    'del_datasource',
    'del_model',
    'del_transformer',
    'get_analysis_list',
    'get_model_list',
    'get_prediction_list',
    'get_transformer_list',
    'make_analysis',
    'make_data',
    'make_predict',
    'make_sources',
    'make_train',
    'pop_prediction',
]
