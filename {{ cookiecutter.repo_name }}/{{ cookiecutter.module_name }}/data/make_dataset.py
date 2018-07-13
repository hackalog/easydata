# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from .datasets import available_datasets, load_dataset, fetch_and_unpack
from ..paths import data_path

@click.command()
@click.argument('action')
def main(action, datasets=None):
    """Fetch and/or process the raw data

    Runs data processing scripts to turn raw data from (../raw) into

    Raw files are downloaded into `project_dir`/data/raw
    Interim files are generated in `project_dir`/data/interim

    action: {'fetch', 'process'}

    """
    logger = logging.getLogger(__name__)
    logger.info(f'Dataset: running {action}')

    if datasets is None:
        datasets = available_datasets

    unpacked_datasets = {}
    for dataset_name in datasets:
        if action == 'fetch':
            unpacked_datasets[dataset_name] = fetch_and_unpack(dataset_name, do_unpack=False)
        elif action == 'process':
            ds = load_dataset(dataset_name)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
