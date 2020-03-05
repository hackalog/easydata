# -*- coding: utf-8 -*-
import click
import json
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

from ..log import logger
from ..utils import save_json
from .. import paths
from .model_list import build_models

@click.command()
@click.argument('model_list')
@click.option('--output_file', '-o', nargs=1, type=str,
              default='trained_models.json')
@click.option('--hash-type', '-H', type=click.Choice(['md5', 'sha1']),
              default='sha1')
def main(model_list, *, output_file, hash_type):
    """Trains models speficied in the supplied `model_list` file

    output is a dictionary of trained model metadata keyed by
    model_key := {algorithm}_{dataset}_{run_number}, where:

    dataset:
        name of dataset to use
    algorithm:
        name of algorithm (estimator) to run on the dataset
    run_number:
        Arbitrary integer.

    The combination of these 3 things must be unique.

    trained models are written to `paths['trained_model_path']`.

    For every model, we write:

    {model_key}.model:
        the trained model
    {model_key}.metadata:
        Metadata for this model

    Parameters
    ----------
    model_list: filename
        json file specifying list of options dictionaries to be passed to
        `train_model`
    output_file: str
        name of json file to write metadata to
    hash_name: {'sha1', 'md5'}
        type of hash to use for caching of python objects


    """
    logger.debug(f'Building models from {model_list}')

    os.makedirs(paths['trained_model_path'], exist_ok=True)

    saved_meta = build_models(model_file=model_list, hash_type=hash_type)

    logger.debug(f"output dir: {model_path}")
    logger.debug(f"output filename: {output_file}")
    if saved_meta:
        save_json(paths['model_path'] / output_file, saved_meta)
        logger.info("Training complete! Access results via workflow.available_models()")

if __name__ == '__main__':

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
