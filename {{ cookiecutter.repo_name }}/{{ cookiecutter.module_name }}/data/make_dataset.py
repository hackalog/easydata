# -*- coding: utf-8 -*-
import click
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from .datasets import process_datasources
from ..log import logger

@click.command()
@click.argument('action')
def main(action, datasources=None):
    """Fetch and/or process the raw data

    Raw files are downloaded into paths['raw_data_path']
    Interim files are generated in paths['interim_data_path']
    Processed data files are saved in paths['processed_data_path']

    action: {'fetch', 'unpack', 'process'}

    """
    process_datasources(datasources=datasources, action=action)

if __name__ == '__main__':
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
