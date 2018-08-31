# -*- coding: utf-8 -*-
import click
import json
import joblib
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

from ..logging import logger
from ..paths import model_path, trained_model_path
from .train import train_model

@click.command()
@click.argument('model_list')
@click.option('--output_file', '-o', nargs=1, type=str)
@click.option('--hash-type', '-H', type=click.Choice(['md5', 'sha1']), default='sha1')
def main(model_list, output_file='trained_models.json', hash_type='sha1'):
    """Trains models speficied in the supplied `model_list` file

    output is a dictionary of trained model metadata

    trained models are written to `trained_model_path`.

    Parameters
    ----------
    model_list: filename
        json file specifying list of options dictionaries to be passed to `train_model`
    output_file: str
        name of json file to write metadata to
    hash_name: {'sha1', 'md5'}
        type of hash to use for caching of python objects


    """
    logger.info(f'Building models from {model_list}')

    os.makedirs(trained_model_path, exist_ok=True)

    with open(model_path / model_list) as f:
        training_dicts = json.load(f)

    for td in training_dicts:
        train_model(**td)

if __name__ == '__main__':

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
