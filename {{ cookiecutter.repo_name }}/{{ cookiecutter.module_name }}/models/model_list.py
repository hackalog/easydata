import pathlib
from ..utils import load_json, save_json
from .. import paths
from ..data import available_datasets
from .algorithms import available_algorithms
from ..log import logger
from .train import train_model, save_model, load_model

__all__ =[
    'get_model_list',
    'del_model',
    'add_model',
    'build_models',
    'available_models',
]

def get_model_list(model_dir=None, model_file=None, include_filename=False):
    """Get the list of model generation pipelines

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
    model_dir: path. (default: MODULE_DIR/data)
        Location of `model_file`
    model_file: string, default 'model_list.json'
        Name of json file that contains the model pipeline
    """
    if model_dir is None:
        model_dir = paths['model_path']
    else:
        model_dir = pathlib.Path(model_dir)

    if model_file is None:
        model_file = 'model_list.json'

    model_file_fq = model_dir / model_file
    try:
        model_list = load_json(model_file_fq)
    except FileNotFoundError:
        model_list = []

    if include_filename:
        return model_list, model_file_fq
    return model_list

def del_model(index, model_dir=None, model_file=None):
    """Delete an entry in the model list

    index: index of entry
    model_dir: path. (default: MODULE_DIR)
        Location of `model_file`
    model_file: string, default 'model_list.json'
        Name of json file that contains the model pipeline
    """
    model_list, model_file_fq = get_model_list(model_dir=model_dir,
                                               model_file=model_file,
                                               include_filename=True)

    del(model_list[index])
    save_json(model_file_fq, model_list)

def add_model(dataset_name=None,
              algorithm_name=None,
              algorithm_params=None,
              model_dir=None, model_file=None,
              run_number=1, force=False):
    """Create and add a dataset transformation pipeline to the workflow.

    Model pipelines apply a sequence of model functions to a Dataset (or RawDataset),
    producing a new Dataset.

    Parameters
    ----------
    dataset_name: string
        Name of dataset to train the model on
    algorithm_name: string
        Name of an algorithm (estimator) given in `available_algorithms()`
    algorithm_params: dict
        Dictionary of options to pass to `algorithm_name`
    force: boolean, default False
        If an identical entry already exists, force it to be added.
    run_numner: int
        A unique integer used to distinguish between different builds with
        otherwise identical parameters
    model_dir: path. (default: MODULE_DIR/data)
        Location of `model_file`
    model_file: string, default 'model_list.json'
        Name of json file that contains the model pipeline
    """
    model_list, model_file_fq = get_model_list(model_dir=model_dir,
                                               model_file=model_file,
                                               include_filename=True)


    if dataset_name is None or algorithm_name is None:
        raise Exception
    if algorithm_params is None:
        algorithm_params = {}
    model = {
        'dataset_name': dataset_name,
        'algorithm_name': algorithm_name,
        'algorithm_params': algorithm_params,
        'run_number': run_number
    }
    if (model in model_list) and not force:
        logger.warning(f"model: {model} is already in the model list." +
                       "Skipping. To force an addition, set force=True")
    else:
        model_list.append(model)
    save_json(model_file_fq, model_list)

def build_models(model_file='model_list.json', model_dir=None, hash_type='sha1'):
    """Build, train, and save models.

    Trained models are written to `paths['trained_model_path']`.

    For every model, we write:

    {model_key}.model:
        the trained model
    {model_key}.metadata:
        Metadata for this model

    Parameters
    ----------
    model_file: filename
        json file specifying list of options dictionaries to be passed to
        `train_model`
    model_dir: path
        location of `model_file`
    hash_name: {'sha1', 'md5', 'sha256'}
        type of hash to use for caching of python objects

    Returns
    -------
    Dictionary of trained model metadata keyed by
    model_key := {algorithm}_{dataset}_{run_number}, where:

    dataset:
        name of dataset to use
    algorithm:
        name of algorithm (estimator) to run on the dataset
    run_number:
        Arbitrary integer.

    The combination of these 3 things must be unique.
    """
    training_dicts = get_model_list(model_dir=model_dir, model_file=model_file)

    dataset_list = available_datasets()
    algorithm_list = available_algorithms()

    metadata_dict = {}  # Used to ensure uniqueness of keys
    for td in training_dicts:
        ds_name = td.get('dataset_name', None)
        assert ds_name in dataset_list, f'Unknown Dataset: {ds_name}'

        alg_name = td.get('algorithm_name', None)
        assert alg_name in algorithm_list, f'Unknown Algorithm: {alg_name}'

        run_number = td.get('run_number', 0)
        model_key = f"{alg_name}_{ds_name}_{run_number}"
        if model_key in metadata_dict:
            raise Exception("{id_base} already exists. Give a unique " +
                            "`run_number` to avoid collisions.")
        else:
            td['run_number'] = run_number
            metadata_dict[model_key] = td

        saved_meta = {}
        for model_key, td in metadata_dict.items():
            logger.info(f'Creating model: {model_key}')
            trained_model, added_metadata = train_model(hash_type=hash_type,
                                                        **td)
            # replace specified params with full set of params used
            td['algorithm_params'] = dict(trained_model.get_params())
            new_metdata = {**td, **added_metadata}
            saved_meta[model_key] = save_model(model_name=model_key,
                                               model=trained_model,
                                               metadata=new_metdata)

    return saved_meta

def available_models(models_dir=None, keys_only=True):
    """Get a list of trained models.

    Parameters
    ----------
    models_dir: path
        location of saved dataset files
    """
    if models_dir is None:
        models_dir = paths['trained_model_path']
    else:
        models_dir = pathlib.Path(models_dir)

    model_dict = {}
    for modelfile in models_dir.glob("*.metadata"):
        model_stem = str(modelfile.stem)
        model_meta = load_model(model_name=model_stem, model_path=models_dir, metadata_only=True)
        model_dict[model_stem] = model_meta

    if keys_only:
        return list(model_dict.keys())
    return model_dict
