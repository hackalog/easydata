import json
import joblib
import pathlib

from ..paths import trained_model_path
from ..utils import save_json

__all__ = [
    'load_model',
    'save_model',
    'train_model'
]

def train_model(**kwargs):
    """Placeholder for training function"""
    pass

def save_model(metadata=None, model_path=None, hash_type='sha1', *, model_name, model):
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
    model_path: path, default `trained_model_path`
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
        model_path = trained_model_path
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
        model_path = trained_model_path
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
