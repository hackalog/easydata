# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from ..utils import save_json, load_json
import click

from ..log import logger
from .. import paths
from .predict import run_predictions

@click.command()
@click.argument('model_list')
@click.option('--output_file', '-o', nargs=1, type=str, default='predictions.json')
@click.option('--hash-type', '-H', type=click.Choice(['md5', 'sha1']), default='sha1')
def main(model_list, *, output_file, hash_type):
    logger.debug(f'Executing models from {model_list}')

    os.makedirs(paths['model_output_path'], exist_ok=True)

    saved_meta = run_predictions(predict_file=model_list, predict_dir=paths['model_path'])

    if saved_meta:
        save_json(paths['model_path'] / output_file, saved_meta)
        logger.info(f"Predict complete! Results accessible via workflow.available_predictions")

if __name__ == '__main__':

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
