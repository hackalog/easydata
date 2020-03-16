# -*- coding: utf-8 -*-
import click
import json
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

from ..log import logger
from ..utils import load_json, save_json
from .. import paths

from .analysis import run_analyses   #, save_df_summary


@click.command()
@click.argument('analysis_list')
@click.option('--output_file', '-o', nargs=1, type=str,
              default='analyses.json')
@click.option('--hash-type', '-H', type=click.Choice(['md5', 'sha1']),
              default='sha1')
def main(analysis_list, *, output_file, hash_type):
    """Runs an  analysis function on a Dataset.

    The supplied `analysis_list` file should be a list of dicts with
    the following key-value pairs.

        analysis_name: name of an  analysis in available_analysiss
        analysis_params: dict of params that the analysis takes

    For every analysis, we write:

    {analysis}.csv:
        analysis output file
    {analysis}.metadata:
        Metadata for what went into this analysis

    Parameters
    ----------
    analysis_list: filename
        json file specifying list of options dictionaries to be passed to
        `train_model`
    output_file: str
        name of json file to write metadata to
    hash_name: {'sha1', 'md5'}
        type of hash to use for caching of python objects


    """
    logger.debug(f'Running summary analysis from {analysis_list}')

    os.makedirs(paths['analysis_path'], exist_ok=True)
    saved_meta = run_analyses(analysis_list=analysis_list)

    if saved_meta:
        save_json(paths['reports_path'] / output_file, saved_meta)
    logger.info("Access results via workflow.available_summaries()")

if __name__ == '__main__':

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
