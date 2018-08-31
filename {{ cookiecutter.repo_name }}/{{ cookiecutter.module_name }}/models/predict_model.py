# -*- coding: utf-8 -*-
import click
import json
import joblib
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from functools import partial

import numpy as np
import pandas as pd

from ..logging import logger
from ..paths import model_path, model_output_path
from ..data import datasets
from . import run_model

@click.command()
@click.argument('model_list')
@click.option('--output_file', '-o', nargs=1, type=str, default='predictions.json')
@click.option('--hash-type', '-H', type=click.Choice(['md5', 'sha1']), default='sha1')
def main(model_list, output_file=None, hash_type='sha1'):
    logger.info(f'Executing models from {model_list}')

    os.makedirs(model_output_path, exist_ok=True)

    with open(model_path / model_list) as f:
        predict_list = json.load(f)

    for exp in predict_list:
        run_model(**exp)

if __name__ == '__main__':

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
