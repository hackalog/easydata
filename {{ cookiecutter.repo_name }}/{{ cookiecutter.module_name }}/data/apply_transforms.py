# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import click
from .. import paths
from ..log import logger
from .transform_data import apply_transforms


@click.command()
@click.argument('transformer_file', default='transformer_list.json')
@click.option('--output_dir', '-o', nargs=1, type=str)
@click.option('--input_dir', '-i', nargs=1, type=str)
@click.option('--hash-type', '-H', type=click.Choice(['md5', 'sha1']), default='sha1')
def main(transformer_file, output_dir=None, input_dir=None, *, hash_type):
    logger.info(f'Transforming datasets from {transformer_file}')

    if output_dir is None:
        output_dir = paths['processed_data_path']
    else:
        output_dir = Path(output_dir)
    if input_dir is None:
        input_dir = paths['catalog_path']
    else:
        input_dir = Path(input_dir)

    os.makedirs(output_dir, exist_ok=True)

    apply_transforms(transformer_path=input_dir, transformer_file=transformer_file, output_dir=output_dir)

if __name__ == '__main__':

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
