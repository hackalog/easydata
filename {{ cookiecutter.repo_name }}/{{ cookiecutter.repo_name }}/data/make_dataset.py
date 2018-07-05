# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from .datasets import fetch_and_unpack, available_datasets

@click.command()
@click.argument('project_dir', type=click.Path(exists=True))
def main(project_dir, datasets=None):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).

    Raw files are downloaded into `project_dir`/data/raw
    Interim files are generated in `project_dir`/data/interim

    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    if datasets is None:
        datasets = available_datasets

    data_dir = Path(project_dir) / 'data'

    unpacked_datasets = {}
    for dataset_name in datasets:
        unpacked_datasets[dataset_name] = fetch_and_unpack(dataset_name, data_dir=data_dir)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
