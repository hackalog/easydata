import joblib
import logging
import os
import pathlib
import sys
import time

from ..paths import processed_data_path
from ..utils import record_time_interval
from .dset import Dataset

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

__all__ = ['run_algorithm']

def run_algorithm(dataset, algorithm_object=None, algorithm_name=None,
                  run_number=0, experiment_info=None, data_path=None,
                  hash_type='sha1',
                  file_base=None, force=False):
    '''
    Runs an algorithm_object on the dataset and returns a new dataset object,
    and saves it to disk under `data_path / file_base`.

    Parameters
    ----------
    dataset: A dataset object containing the data to run the algorithm on.
    algorithm_name: (str, optional) name of the algorithm used for the given
        vector space embedding
    algorithm_object: instance of the algorithm. For example, an
        instance of sklearn.decomposition.PCA. This object should have
        a `fit_transform` method and a `__repr__()`.
    experiment_info: (str)
        any other information to note about the experiment
        This is used as the output dataset's DESCR text
    file_base: (str, optional) filename base for the output dataset.
        Will also be used as the output `dataset.name`.
    run_number: (int) attempt number via the same parameters
    data_path: (path) base path for save the output datset to
    force: (boolean) force re-running the algorithm and overwriting
        any existing data.

    Returns
    -------
    Dataset object with experiment dictionary in metadata
    '''
    if data_path is None:
        data_path = processed_data_path
    else:
        data_path = pathlib.Path(data_path)

    if algorithm_object is None:
        raise ValueError('`algorithm_object` is required')
    algorithm_repr = algorithm_object.__repr__()
    if algorithm_name is None:
        algorithm_name = str(algorithm_repr).split('(')[0]
    if file_base is None:
        file_base = f'{dataset.name}_{algorithm_name}_{run_number}'

    # add experiment metadata
    experiment = {
        'algorithm_name': algorithm_name,
        'algorithm_object': algorithm_repr,
        'hash_type': hash_type,
        'data_hash': joblib.hash(dataset.data, hash_name=hash_type),
        'target_hash': joblib.hash(dataset.target, hash_name=hash_type),
        'run_number': run_number,
        }

    metadata_fq = data_path / f'{file_base}.metadata'

    if metadata_fq.exists() and force is False:
        cached_metadata = Dataset.load(file_base, data_path=data_path, metadata_only=True)
        if experiment.items() <= cached_metadata['experiment'].items():
            logger.info("Experiment has already been run. Returning Cached Result")
            return Dataset.load(file_base, data_path=data_path)
        else:
            raise Exception(f'An Experiment with this name exists already, '
                            'but metadata has changed. '
                            'Use `force=True` to overwrite, or change one of '
                            '`run_number` or `file_base`')

    # Either force is True, or we need to rerun the algorithm.
    start_time = time.time()
    exp_data = algorithm_object.fit_transform(dataset.data)
    end_time = record_time_interval(algorithm_name, start_time)

    experiment['start_time'] = start_time
    experiment['duration'] = end_time - start_time

    new_metadata = dataset.metadata.copy()
    new_metadata['experiment'] = experiment
    new_dataset = Dataset(dataset_name=file_base, data=exp_data,
                          target=dataset.target, metadata=new_metadata,
                          descr_txt=experiment_info)
    new_dataset.dump(file_base=file_base, data_path=data_path, force=True)
    return new_dataset
