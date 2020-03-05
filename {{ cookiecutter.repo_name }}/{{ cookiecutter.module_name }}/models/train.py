import json
import joblib
import pathlib
import time

from .. import paths
from ..utils import save_json, load_json, record_time_interval
from ..data import Dataset, available_datasets
from .algorithms import available_algorithms
from ..log import logger

__all__ = [
    'load_model',
    'save_model',
    'train_model',
]

def train_model(algorithm_params=None,
                run_number=0, *, dataset_name, algorithm_name, hash_type,
                **kwargs):
    """Train a model using the specified algorithm using the given dataset.

    """
    metadata = {}
    ds = Dataset.load(dataset_name)
    metadata['data_hash'] = joblib.hash(ds.data, hash_name=hash_type)
    metadata['target_hash'] = joblib.hash(ds.target, hash_name=hash_type)
    model = available_algorithms(keys_only=False)[algorithm_name]
    model.set_params(**algorithm_params)
    start_time = time.time()
    model.fit(ds.data, y=ds.target)
    end_time = record_time_interval('train_model', start_time)
    metadata['start_time'] = start_time
    metadata['duration'] = end_time - start_time
    return model, metadata


def save_model(metadata=None, model_path=None, hash_type='sha1',
               *, model_name, model):
    """Save a model to disk

    Parameters
    ----------
    model_name: str
        Unique key to use as model name (and filename)
    metadata: dict
        Model metadata
    model:
        sklearn estimator representing a model
    hash_type: {'sha1', 'md5'}
        hash algorithm to use for joblib hashing
    model_path: path, default `paths['trained_model_path']`
        Where model should be saved.

    Returns
    -------
    copy of metadata
    """
    if metadata is None:
        metadata = {}
    else:
        metadata = metadata.copy()

    if model_path is None:
        model_path = paths['trained_model_path']
    else:
        model_path = pathlib.Path(model_path)

    joblib.dump(model, model_path / f"{model_name}.model")
    metadata['model_hash'] = joblib.hash(model, hash_name=hash_type)
    save_json(model_path / f"{model_name}.metadata", metadata)
    return metadata


def load_model(model_name=None, metadata_only=False, model_path=None):
    """Load a model (or model metadata)

    Parameters
    ----------
    metadata_only: boolean
        If True, just return the model metadata.
    model_path:
    model_name:

    Returns
    -------
    If `metadata_only` is True:

        dict containing model_metadata

    else:

        The tuple (model, model_metadata)
    """
    if model_name is None:
        raise Exception("model_name must be specified")
    if model_path is None:
        model_path = paths['trained_model_path']
    else:
        model_path = pathlib.Path(model_path)

    fq_metadata = model_path / f'{model_name}.metadata'
    fq_model = model_path / f'{model_name}.model'
    if not fq_metadata.exists():
        raise FileNotFoundError(f"Could not find model metadata: {model_name}")

    with open(fq_metadata, 'r') as f:
        model_metadata = json.load(f)

    if metadata_only is True:
        return model_metadata

    if not fq_model.exists():
        raise FileNotFoundError(f"Could not find model: {model_name}")

    model = joblib.load(fq_model)

    return model, model_metadata
