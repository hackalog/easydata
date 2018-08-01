from functools import partial
import gzip
import hashlib
import json
import logging
import os
import pathlib
import shutil
import sys
import tarfile
import zipfile
import zlib

from ..paths import interim_data_path, raw_data_path

_MODULE = sys.modules[__name__]
_MODULE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

hash_function_map = {
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'md5': hashlib.md5,
}

def hash_file(fname, algorithm="sha1", block_size=4096):
    '''Compute the hash of an on-disk file

    algorithm: {'md5', sha1', 'sha256'}
        hash algorithm to use
    block_size:
        size of chunks to read when hashing

    Returns:
        Hashlib object
    '''
    hashval = hash_function_map[algorithm]()
    with open(fname, "rb") as fd:
        for chunk in iter(lambda: fd.read(block_size), b""):
            hashval.update(chunk)
    return hashval

def unpack(filename, dst_dir=None, create_dst=True):
    '''Unpack a compressed file

    filename: path
        file to unpack
    dst_dir: path (default paths.interim_data_path)
        destination directory for the unpack
    create_dst: boolean
        create the destination directory if needed
    '''
    if dst_dir is None:
        dst_dir = interim_data_path

    if create_dst:
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

    # in case it is a Path
    path = str(filename)

    archive = False
    if path.endswith('.zip'):
        archive = True
        opener, mode = zipfile.ZipFile, 'r'
    elif path.endswith('.tar.gz') or path.endswith('.tgz'):
        archive = True
        opener, mode = tarfile.open, 'r:gz'
    elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
        archive = True
        opener, mode = tarfile.open, 'r:bz2'
    elif path.endswith('.tar'):
        archive = True
        opener, mode = tarfile.open, 'r'
    elif path.endswith('.gz'):
        opener, mode = gzip.open, 'rb'
        outfile, outmode = path[:-3], 'wb'
    elif path.endswith('.Z'):
        logger.warning(".Z files are only supported on systems that ship with gzip. Trying...")
        os.system(f'gzip -d {path}')
        opener, mode = open, 'rb'
        path = path[:-2]
        outfile, outmode = path, 'wb'
    else:
        opener, mode = open, 'rb'
        outfile, outmode = path, 'wb'
        logger.info("No compression detected. Copying...")

    with opener(path, mode) as f_in:
        if archive:
            logger.info(f"Extracting {filename.name}")
            f_in.extractall(path=dst_dir)
        else:
            outfile = pathlib.Path(outfile).name
            logger.info(f"Decompresing {outfile}")
            with open(pathlib.Path(dst_dir) / outfile, outmode) as f_out:
                shutil.copyfileobj(f_in, f_out)

def head_file(filename, n=5):
    """Return the first `n` lines of a file
    """
    with open(filename, 'r') as fd:
        lines = []
        for i, line in enumerate(fd):
            if i > n:
                break
            lines.append(line)
    return "".join(lines)

def list_dir(path, fully_qualified=False, glob_pattern='*'):
    """do an ls on a path

    fully_qualified: boolean (default: False)
        If True, return a list of fully qualified pathlib objects.
        if False, return just the bare filenames
    glob_pattern: glob (default: '*')
        File mattern to match

    Returns
    -------
    A list of names, or fully qualified pathlib objects"""
    if fully_qualified:
        return list(pathlib.Path(path).glob(glob_bpattern))
    else:
        return [file.name for file in pathlib.Path(path).glob(glob_pattern)]
