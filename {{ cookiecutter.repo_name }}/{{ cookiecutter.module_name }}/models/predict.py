import joblib
import json
import os
import pathlib
import time

from ..data import Dataset
from ..log import logger
from .. import paths
from ..utils import record_time_interval, save_json
from .train import load_model
from .model_list import get_model_list
from ..data import available_datasets

__all__ = [
    'run_model',
    'run_predictions',
    'add_prediction',
    'get_prediction_list',
    'pop_prediction',
    'available_predictions',
]

def run_model(experiment_info=None,
              output_dataset=None,
              force=False,
              hash_type='sha1',
              output_path=None,
              run_number=1,
              *,
              dataset_name,
              is_supervised,
              model_name):
    '''Run a model on a dataset (predict/transform)

    Runs an algorithm_object on the dataset and returns a new
    dataset object, tagged with experiment metadata,
    and saves it to disk under `data_path / output_dataset`.

    Parameters
    ----------
    dataset_name: str, valid dataset name
        Name of a dataset object that will be run through the model
    model_name: str, valid model name
        name of the model that will transform the data
    experiment_info: (str)
        any other information to note about the experiment
        This is used as the output dataset's DESCR text
    output_path: path
        directory to store output files
    output_dataset: (str, optional) filename base for the output dataset.
        Will also be used as the output `dataset.name`.
    run_number: (int)
        attempt number via the same parameters
    force: (boolean)
        force re-running the algorithm and overwriting any existing data.

    Returns
    -------
    Dataset object emerging from the model,
    with experiment dictionary embedded in metadata
    '''
    if output_path is None:
        output_path = paths['model_output_path']
    else:
        output_path = pathlib.Path(output_path)

    if output_dataset is None:
        output_dataset = f'{model_name}_exp_{dataset_name}_{run_number}'

    os.makedirs(output_path, exist_ok=True)

    dataset = Dataset.load(dataset_name)

    model, model_meta = load_model(model_name)

    # add experiment metadata
    experiment = {
        'model_name': model_name,
        'dataset_name': dataset_name,
        'run_number': run_number,
        'hash_type': hash_type,
        'input_data_hash': joblib.hash(dataset.data, hash_name=hash_type),
        'input_target_hash': joblib.hash(dataset.target, hash_name=hash_type),
        'model_hash': joblib.hash(model, hash_name=hash_type),
    }
    logger.debug(f"Predict: Applying {model_name} to {dataset_name}")
    metadata_fq = output_path / f'{output_dataset}.metadata'

    if metadata_fq.exists() and force is False:
        cached_metadata = Dataset.load(output_dataset, data_path=output_path,
                                       metadata_only=True)
        if experiment.items() <= cached_metadata['experiment'].items():
            logger.info("Experiment has already been run. Returning Cached Result")
            return Dataset.load(output_dataset, data_path=output_path)
        else:
            raise Exception(f'An Experiment with name {output_dataset} exists already, '
                            'but metadata has changed. '
                            'Use `force=True` to overwrite, or change one of '
                            '`run_number` or `output_dataset`')

    # Either force is True, or we need to rerun the algorithm.
    start_time = time.time()
    if is_supervised:
        exp_data = model.predict(dataset.data)
    else:
        if hasattr(model, 'transform'):
            logger.debug('Transform found. Skipping fit')
            exp_data = model.transform(dataset.data)
        else:
            logger.debug('No Transform found. Running fit_transform')
            exp_data = model.fit_transform(dataset.data)

    end_time = record_time_interval(output_dataset, start_time)

    experiment['start_time'] = start_time
    experiment['duration'] = end_time - start_time

    new_metadata = dataset.metadata.copy()
    new_metadata['experiment'] = experiment
    if experiment_info:
        new_metadata['descr'] = experiment_info
    new_dataset = Dataset(dataset_name=output_dataset, data=exp_data,
                          target=dataset.target.copy(), metadata=new_metadata)
    new_dataset.dump(file_base=output_dataset, dump_path=output_path, force=True)
    return new_dataset


def load_prediction(predict_name=None, metadata_only=False, predict_path=None):
    """Load a prediction (or prediction metadata)

    Parameters
    ----------
    metadata_only: boolean
        If True, just return the prediction metadata.
    predict_path:
    predict_name:

    Returns
    -------
    If `metadata_only` is True:

        dict containing predict_metadata

    else:

        The tuple (predict, predict_metadata)
    """
    if predict_name is None:
        raise Exception("predict_name must be specified")
    if predict_path is None:
        predict_path = paths['model_output_path']
    else:
        predict_path = pathlib.Path(predict_path)

    fq_predict = predict_path / f'{predict_name}'

    predict = Dataset.load(fq_predict, data_path=predict_path, metadata_only=metadata_only)

    return predict

def run_predictions(force=False, *, predict_file='predict_list.json', predict_dir=None):
    """
    """
    if predict_dir is None:
        predict_dir = paths['model_path']
    else:
        predict_dir = pathlib.Path(predict_dir)

    predict_list = get_prediction_list(model_dir=predict_dir, prediction_file=predict_file)

    saved_meta = {}
    metadata_keys = ['dataset_name', 'hash_type', 'data_hash', 'target_hash', 'experiment']
    for exp in predict_list:
        ds = run_model(**exp, force=force)
        name = ds.metadata['dataset_name']
        metadata = {}
        for key in metadata_keys:
            metadata[key] = ds.metadata[key]
            saved_meta[name] = metadata

    return saved_meta

def get_prediction_list(model_dir=None, prediction_file=None, include_filename=False):
    """Get the list of prediction pipelines

    Returns
    -------
    If include_filename is True:
        A tuple: (model_list, model_file_fq)
    else:
        model_list

    Parameters
    ----------
    include_filename: boolean
        if True, returns a tuple: (list, filename)
    model_dir: path. (default: MODULE_DIR)
        Location of `model_file`
    prediction_file: string, default 'predict_list.json'
        Name of json file that contains the prediction pipeline
    """
    if model_dir is None:
        model_dir = paths['model_path']
    else:
        model_dir = pathlib.Path(model_dir)

    if prediction_file is None:
        prediction_file = 'predict_list.json'

    return get_model_list(model_dir=model_dir, model_file=prediction_file, include_filename=include_filename)

def pop_prediction(index=-1, model_dir=None, prediction_file=None):
    """pop an entry from the prediction list

    index: index of entry
    model_dir: path. (default: MODULE_DIR)
        Location of `model_file`
    prediction_file: string, default 'model_list.json'
        Name of json file that contains the model pipeline
    """
    predict_list, predict_file_fq = get_prediction_list(model_dir=model_dir,
                                                        prediction_file=prediction_file,
                                                        include_filename=True)
    item = predict_list.pop(index)
    save_json(predict_file_fq, predict_list)
    return item

def add_prediction(dataset_name=None,
                   model_name=None,
                   model_dir=None, model_file='predict_list.json',
                   is_supervised=True,
                   output_dataset=None,
                   force=False):
    """Create and add a prediction (experiment) to the prediction list.

    Predictions involve passing a Dataset through a (trained) model
    producing a new Dataset.

    Parameters
    ----------
    dataset_name: string
        Name of dataset to train the model on
    output_dataset: string
        Name to use for output dataset.
    model_name: string
        Name of an model to use, given by `available_models()`
    is_supervised: boolean
        if True, the algorithm's `predict()` method will be used to obtain the output.
        If False, the algorithm's `transform()` method will be used instead
    model_dir: path. (default: MODULE_DIR/data)
        Location of `model_file`
    model_file: string, default 'model_list.json'
        Name of json file that contains the model pipeline
    force: boolean, default False
        Force the addition of a prediction to the predict list
    """
    if model_dir is None:
        model_dir = paths['model_path']

    model_list, model_file_fq = get_model_list(model_dir=model_dir,
                                               model_file=model_file,
                                               include_filename=True)

    if dataset_name is None or model_name is None:
        raise Exception

    prediction = {
        'dataset_name': dataset_name,
        'model_name': model_name,
        'is_supervised': is_supervised,
        'output_dataset': output_dataset,
    }
    if (prediction in model_list) and not force:
        logger.warning(f"prediction: {prediction} is already in the prediction list. " +
                       "Skipping. To force an addition, set force=True")
    else:
        model_list.append(prediction)

    save_json(model_file_fq, model_list)

def available_predictions(models_dir=None, keys_only=True):
    """Get a list of prediction datasets.

    Parameters
    ----------
    models_dir: path
        location of saved prediction files
    """
    if models_dir is None:
        models_dir = paths['model_output_path']
    return available_datasets(dataset_path=models_dir, keys_only=keys_only)
