import pathlib
import pandas as pd

from ..log import logger
from ..data import Dataset
from .. import paths
from ..models.predict import available_predictions
from ..models.model_list import load_model
from ..utils import load_json, save_json
from ..models.model_list import get_model_list

from sklearn.metrics import accuracy_score

__all__ = [
    'available_scorers',
    'available_analyses',
    'get_analysis_list',
    'run_analyses',
    'add_analysis',
]

def available_analyses(keys_only=True):
    """An analysis converts a Dataset to data.

    The input Datasets are typically the results of predictions or transformations.
    The output data may consist of tables, (pandas DataaFrames, CSV files), summary data,
    images, or other output formats.

    This function exists to document the mapping of analysis  names (strings) to the
    underlying analysis function.

    Parameters
    ----------
    keys_only: boolean
        If True, returns a list of valid strings.
        If False, returns a dict mapping these strings to score functions

    Analysis Functions
    ------------------
    'score_predictions': score_predictions
    """
    _ANALYSES = {
        'score_predictions': score_predictions,
    }
    if keys_only:
        return list(_ANALYSES.keys())
    return _ANALYSES

def available_scorers(keys_only=True):
    """A  "scorer" is a function with the signature:
    `score_func(y, y_pred, **kwargs)`

    This function exists to document the mapping of scorer names (strings) to the
    underlying score function:

    Parameters
    ----------
    keys_only: boolean
        If True, returns a list of valid strings.
        If False, returns a dict mapping these strings to score functions

    Scoring Functions
    -----------------
    'accuracy_score': sklearn.metrics.accuracy_score
    """
    _SCORERS = {
        'accuracy_score': accuracy_score,
    }
    if keys_only:
        return list(_SCORERS.keys())
    return _SCORERS

def add_analysis(analysis_name=None, analysis_params=None,
                 analysis_dir=None, analysis_list='analysis_list.json',
                 force=False):
    """Add an Analysis"""
    if analysis_params is None:
        analysis_params = {}
    if analysis_dir is None:
        analysis_dir = paths['analysis_path']
    else:
        analysis_dir = pathlib.Path(analysis_dir)

    analysis_list, analysis_file_fq = get_model_list(model_dir=analysis_dir,
                                                     model_file=analysis_list,
                                                     include_filename=True)
    analysis = {
        'analysis_name': analysis_name,
        'analysis_params': analysis_params,
    }
    if (analysis in analysis_list) and not force:
        logger.warning(f"Analysis: {analysis} is already in the analysis list." +
                       "Skipping. To force an addition, set force=True")
    else:
        analysis_list.append(analysis)


    save_json(analysis_file_fq, analysis_list)

def run_analyses(analysis_dir=None, analysis_list='analysis_list.json'):
    if analysis_dir is None:
        analysis_dir = paths['analysis_path']
    else:
        analysis_dir = pathlib.Path(analysis_dir)

    analysis_list = load_json(analysis_dir / analysis_list)

    saved_meta= {}
    for analysis_dict in analysis_list:
        logger.info(f"Performing Analysis: {analysis_dict['analysis_name']}")
        output, output_dict = run_analysis(**analysis_dict)
        saved_meta[output] = output_dict
    return saved_meta


def run_analysis(analysis_name=None, analysis_params=None):
    '''
    Run a analysis on the given params.
    '''
    output, output_dict = available_analyses(keys_only=False)[analysis_name](**analysis_params)
    if analysis_params:
        analysis_params = {**analysis_params, **output_dict}
    else:
        analysis_params = output_dict
    return output, {'analysis_name':analysis_name, 'analysis_params': analysis_params}

def save_df_summary(df, meta, summary_path):
    name = meta['analysis_name']
    df.to_csv(summary_path / name)
    return name + '.csv'


def score_predictions(predictions_list=None,
                      predictions_dir=None,
                      score_list=None,
                      model_dir=None,
                      csv_file='score_predictions.csv',
                      csv_dir=None,
):
    '''
    Apply scoring functions to the output of predictions, producing a CSV

    A scorer is a function with the signature:
    `score_func(y, y_pred, **kwargs)`

    Parameters
    ---------
    predictions_list: list or None
        list of predictions to compare. Should be a subset
        of the available_predictions.
        Default is everything listed in `available_predictions()`
    score_list: list or None
        List of scorers to use when comparing predicted output vs. real labels
        Default everything in `available_scorers()`
    model_dir:
        path to the trained models
    predictions_dir:
        path to the prediction outputs
    csv_file: filename
        if None, defaults to 'score_predictions.csv'
    csv_dir: path
        If None, assumes paths['summary_path']

    Returns
    -------
    filenames of created data
    '''
    analysis_metadata = {}

    if predictions_dir is None:
        predictions_dir = paths['model_output_path']
    else:
        analysis_metadata['predictions_dir'] = str(predictions_dir)
        predictions_dir = pathlib.Path(predictions_dir)

    if model_dir is None:
        model_dir = paths['trained_model_path']
    else:
        analysis_metadata['model_dir'] = str(model_dir)
        model_dir = pathlib.Path(model_dir)

    if csv_dir is None:
        csv_dir = paths['summary_path']
    else:
        analysis_metadata['csv_dir'] = str(csv_dir)
        csv_dir = pathlib.Path(csv_dir)

    if predictions_list is None:
        predictions_list = available_predictions(keys_only=False, models_dir=predictions_dir)
    analysis_metadata['predictions_list'] = list(predictions_list.keys())

    if score_list is None:
        score_list = available_scorers()

    analysis_metadata['score_list'] = score_list

    score_df = pd.DataFrame(columns=['score_name', 'algorithm_name', 'dataset_name',
                                     'model_name', 'run_number'])
    for current_scorer_name in score_list:
        current_scorer = available_scorers(keys_only=False)[current_scorer_name]
        score_dict = {}
        score_dict['score_name'] = current_scorer_name
        for prediction_name in predictions_list:
            logger.info(f"Scoring: Applying {current_scorer_name} to {prediction_name}")
            prediction = predictions_list[prediction_name]
            exp = prediction['experiment']
            pred_ds = Dataset.load(prediction['dataset_name'],
                                   data_path=predictions_dir)

            ds_name = exp['dataset_name']
            ds = Dataset.load(ds_name)
            score_dict['dataset_name'] = ds_name

            score_dict['score'] = current_scorer(ds.target, pred_ds.data)
            model_metadata = load_model(model_name=exp['model_name'],
                                        metadata_only=True,
                                        model_path=model_dir)
            score_dict['algorithm_name'] = model_metadata['algorithm_name']
            score_dict['model_name'] = exp['model_name']
            score_dict['run_number'] = exp['run_number']
            new_score_df = pd.DataFrame(score_dict, index=[0])
            score_df = score_df.append(new_score_df, sort=True)
    csv_file_fq = csv_dir / csv_file
    logger.info(f"Writing Analysis to {csv_file}")
    score_df.to_csv(csv_file_fq, index=False)
    return (csv_file_fq.name, analysis_metadata)

def get_analysis_list(analysis_dir=None, analysis_file=None, include_filename=False):
    """Get the list of analysis pipelines

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
    analysis_dir: path. (default: MODULE_DIR)
        Location of `model_file`
    analysis_file: string, default 'predict_list.json'
        Name of json file that contains the analysis pipeline
    """
    if analysis_dir is None:
        analysis_dir = paths['analysis_path']
    else:
        analysis_dir = pathlib.Path(analysis_dir)

    if analysis_file is None:
        analysis_file = 'analysis_list.json'

    return get_model_list(model_dir=analysis_dir, model_file=analysis_file,
                          include_filename=include_filename)
