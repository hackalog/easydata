"""
Functions for handling "fileset" data; i.e.  collections of raw files associated with a Dataset
"""

from collections import defaultdict
import pathlib
import shutil
import os

from tqdm.auto import tqdm

from .. import paths
from ..log import logger

__all__ = [
    'process_fileset_files',
]

def process_fileset_files(*, extract_dir=None, metadata=None, unpack_dir=None, file_glob="*", fileset_dir=".fileset", dataset_dir=None, do_copy=False):
    """
    Process unpacked raw files into its minimal dataset components (data, target, metadata).
    Here, 'minimal' means `data` and `target` will be None, and `fileset` will contain a
    file dict of files matching the specified file_glob (and their sizes).

    Parameters
    ----------
    unpack_dir: default paths['interim_data_path']
        The directory the interim data files have been unpacked into
    dataset_dir: default paths['processed_data_path']
        location of processed datasets.
    extract_dir:
        Name of the directory of the unpacked zip file containing the raw data files.
        relative to unpack_dir
    file_glob: string
        Add only files matching this glob pattern to FILESET
    fileset_dir: string
        Used in building the file_dict keys.
    do_copy: boolean
        if True, actually copy the files. Otherwise just build FILESET

    Returns
    -------
    (data, target, additional_metadata)

    where

    data and target are None,

    metadata contains a file dict; i.e.
    'fileset': {"path_relative_to_processed_dir_1": {"filename_1":["size:33"], "filename_2":["size:54"], ...}, ...}
    """
    if metadata is None:
        metadata = {}

    if dataset_dir is None:
        dataset_dir = paths['processed_data_path']
    else:
        dataset_dir = pathlib.Path(dataset_dir)
    if unpack_dir is None:
        unpack_dir = paths['interim_data_path']
    else:
        unpack_dir = pathlib.Path(unpack_dir)
    if extract_dir is not None:
        unpack_dir /= extract_dir

    fileset_dir = pathlib.Path(fileset_dir)
    fileset_dir_fq = dataset_dir / fileset_dir
    logger.debug(f"Do copy: {do_copy}")
    if do_copy:
        if fileset_dir_fq.is_dir():
            logger.warning(f"Cleaning contents of {fileset_dir}")
            shutil.rmtree(fileset_dir_fq)
            logger.debug(f"Copying files to {fileset_dir_fq}...")

    file_dict = defaultdict(dict)
    files = sorted(list(unpack_dir.rglob(file_glob)))
    for i, file in enumerate(tqdm(files)):
        if file.is_dir():
            continue
        relative_path = file.relative_to(unpack_dir)
        fileset_path = fileset_dir / relative_path
        file_dict[str(fileset_path.parent)][str(fileset_path.name)] = [f'size:{os.path.getsize(file)}']
        if do_copy:
            os.makedirs(dataset_dir / fileset_path.parent, exist_ok=True)
            shutil.copyfile(file, dataset_dir / fileset_path)
    metadata['fileset'] = dict(file_dict)

    return None, None, metadata
