import hashlib
import gzip
import os
import pathlib
import shutil
import tarfile
import zipfile
import zlib
import requests

from ..paths import raw_data_path, interim_data_path
from ..logging import logger

__all__ = [
    'available_hashes',
    'fetch_file',
    'fetch_files',
    'fetch_text_file',
    'get_dataset_filename',
    'hash_file',
    'unpack'
]

_HASH_FUNCTION_MAP = {
    'md5': hashlib.md5,
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
}

def available_hashes():
    """Valid Hash Functions

    This function simply returns the dict known hash function
    algorithms.

    It exists to allow for a description of the mapping for
    each of the valid strings.

    The hash functions are:

    ============     ====================================
    Algorithm        Function
    ============     ====================================
    md5              hashlib.md5
    sha1             hashlib.sha1
    sha256           hashlib.sha256
    ============     ====================================

    >>> list(available_hashes().keys())
    ['md5', 'sha1', 'sha256']
    """
    return _HASH_FUNCTION_MAP

def hash_file(fname, algorithm="sha1", block_size=4096):
    '''Compute the hash of an on-disk file

    algorithm: {'md5', sha1', 'sha256'}
        hash algorithm to use
    block_size:
        size of chunks to read when hashing

    Returns:
        Hashlib object
    '''
    hashval = _HASH_FUNCTION_MAP[algorithm]()
    with open(fname, "rb") as fd:
        for chunk in iter(lambda: fd.read(block_size), b""):
            hashval.update(chunk)
    return hashval

def fetch_files(force=False, dst_dir=None, **kwargs):
    '''
    fetches a list of files via URL

    url_list: list of dicts, each containing:
        url:
            url to be downloaded
        hash_type:
            Type of hash to compute
        hash_value: (optional)
            if specified, the hash of the downloaded file will be
            checked against this value
        name: (optional)
            Name of this dataset component
        raw_file:
            output file name. If not specified, use the last
            component of the URL

    Examples
    --------
    >>> fetch_files()
    Traceback (most recent call last):
      ...
    Exception: One of `file_name` or `url` is required
    '''
    url_list = kwargs.get('url_list', None)
    if not url_list:
        return fetch_file(force=force, dst_dir=dst_dir, **kwargs)
    result_list = []
    for url_dict in url_list:
        name = url_dict.get('name', None)
        if name is None:
            name = url_dict.get('url', 'dataset')
        logger.debug(f"Ready to fetch {name}")
        result_list.append(fetch_file(force=force, dst_dir=dst_dir, **url_dict))
    return all([r[0] for r in result_list]), result_list

def fetch_text_file(url, file_name=None, dst_dir=None, force=True, **kwargs):
    """Fetch a text file (via URL) and return it as a string.

    Arguments
    ---------

    file_name:
        output file name. If not specified, use the last
        component of the URL
    dst_dir:
        directory to place downloaded files
    force: boolean
        normally, the URL is only downloaded if `file_name` is
        not present on the filesystem, or if the existing file has a
        bad hash. If force is True, download is always attempted.

    In addition to these options, any of `fetch_file`'s keywords may
    also be passed

    Returns
    -------
    fetched string, or None if something went wrong with the download
    """
    retlist = fetch_file(url, file_name=file_name, dst_dir=dst_dir,
                         force=force, **kwargs)
    if retlist[0]:
        _, filename, _ = retlist
        with open(filename, 'r') as txt:
            return txt.read()
    else:
        logger.warning(f'fetch of {url} failed with status: {retlist[0]}')
        return None

def fetch_file(url=None, contents=None,
               file_name=None, dst_dir=None,
               force=False, source_file=None,
               hash_type="sha1", hash_value=None,
               **kwargs):
    '''Fetch raw file entries.

    Files can be specified by `url`, `source_file` name, or via `contents` (string)

    if `file_name` already exists, compute the hash of the on-disk file

    contents:
        contents of file to be created
    url:
        url to be downloaded
    hash_type:
        Type of hash to compute
    hash_value: (optional)
        if specified, the hash of the downloaded file will be
        checked against this value
    name: (optional)
        Name of this dataset component
    file_name:
        output file name. If not specified, use the last
        component of the URL
    dst_dir:
        directory to place downloaded files
    force: boolean
        normally, the URL is only downloaded if `file_name` is
        not present on the filesystem, or if the existing file has a
        bad hash. If force is True, download is always attempted.
    source_file: path
        Path to source file. Will be copied to `raw_data_path`

    Returns
    -------
    one of:
        (HTTP_Code, downloaded_filename, hash) (if downloaded from URL)
        (True, filename, hash) (if already exists)
        (False, [error], None)

    Examples
    --------
    >>> fetch_file()
    Traceback (most recent call last):
      ...
    Exception: One of `file_name` or `url` is required
    '''
    if dst_dir is None:
        dst_dir = raw_data_path
    if file_name is None:
        if url:
            file_name = url.split("/")[-1]
            logger.debug(f"`file_name` not specified. Inferring from URL: {file_name}")
        elif source_file:
            file_name = str(pathlib.Path(source_file).name)
            logger.debug(f"`file_name` not specified. Inferring from `source_file`: {file_name}")
        else:
            raise Exception('One of `file_name`, `url`, or `source_file` is required')
    dl_data_path = pathlib.Path(dst_dir)

    if not os.path.exists(dl_data_path):
        os.makedirs(dl_data_path)

    raw_data_file = dl_data_path / file_name

    if contents is not None:
        logger.debug(f'Creating {raw_data_file.name} from `contents` string')
        with open(raw_data_file, 'w') as fw:
            fw.write(contents)

    if raw_data_file.exists():
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        if hash_value is not None:
            if raw_file_hash == hash_value:
                if force is False:
                    logger.debug(f"{file_name} already exists and hash is valid")
                    return True, raw_data_file, raw_file_hash
            else:
                logger.warning(f"{file_name} exists but has bad hash {raw_file_hash}."
                               " Re-fetching")
        else:
            if force is False:
                logger.debug(f"{file_name} exists, but no hash to check. "
                             f"Setting to {hash_type}:{raw_file_hash}")
                return True, raw_data_file, raw_file_hash

    if url is None and contents is None and source_file is None:
        raise Exception(f"Cannot proceed: {file_name} not found on disk, and no fetch information (`url` or `source_file`, or `contents`) specified.")

    if url is not None:
        # Download the file
        try:
            results = requests.get(url)
            results.raise_for_status()
            raw_file_hash = _HASH_FUNCTION_MAP[hash_type](results.content).hexdigest()
            if hash_value is not None:
                if raw_file_hash != hash_value:
                    logger.error(f"Invalid hash on downloaded {file_name}"
                                 f" {hash_type}:{raw_file_hash} != {hash_type}:{hash_value}")
                    return False, f"Bad Hash: {hash_type}:{raw_file_hash}", None
            with open(raw_data_file, "wb") as code:
                code.write(results.content)
        except requests.exceptions.HTTPError as err:
            return False, err, None
    elif contents is not None:
        with open(raw_data_file, 'w') as fw:
            fw.write(contents)
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        return True, raw_data_file, raw_file_hash
    elif source_file is not None:
        shutil.copyfile(source_file, raw_data_file)
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        source_file = pathlib.Path(source_file)
        logger.debug(f"Copying {source_file.name} to raw_data_path")
        return True, raw_data_file, raw_file_hash
    else:
        raise Exception('One of `url` or `contents` must be specified')

    logger.debug(f'Retrieved {raw_data_file.name} (hash '
                 f'{hash_type}:{raw_file_hash})')
    return results.status_code, raw_data_file, raw_file_hash

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
    verb = "Copying"
    if path.endswith('.zip'):
        archive = True
        verb = "Unzipping"
        opener, mode = zipfile.ZipFile, 'r'
    elif path.endswith('.tar.gz') or path.endswith('.tgz'):
        archive = True
        verb = "Untarring and ungzipping"
        opener, mode = tarfile.open, 'r:gz'
    elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
        archive = True
        verb = "Untarring and unbzipping"
        opener, mode = tarfile.open, 'r:bz2'
    elif path.endswith('.tar'):
        archive = True
        verb = "Untarring"
        opener, mode = tarfile.open, 'r'
    elif path.endswith('.gz'):
        verb = "Ungzipping"
        opener, mode = gzip.open, 'rb'
        outfile, outmode = path[:-3], 'wb'
    elif path.endswith('.Z'):
        verb = "Uncompressing"
        logger.warning(".Z files are only supported on systems that ship with gzip. Trying...")
        os.system(f'gzip -f -d {path}')
        opener, mode = open, 'rb'
        path = path[:-2]
        outfile, outmode = path, 'wb'
    else:
        opener, mode = open, 'rb'
        outfile, outmode = path, 'wb'

    with opener(path, mode) as f_in:
        if archive:
            f_in.extractall(path=dst_dir)
            logger.debug(f"Extracting {filename.name}")
        else:
            outfile = pathlib.Path(outfile).name
            logger.debug(f"{verb} {outfile}")
            with open(pathlib.Path(dst_dir) / outfile, outmode) as f_out:
                shutil.copyfileobj(f_in, f_out)

def get_dataset_filename(ds_dict):
    """Figure out the downloaded filename for a dataset entry

    if a `file_name` key is present, use this,
    otherwise, use the last component of the `url`

    Returns the filename

    Examples
    --------
    >>> ds_dict = {'url': 'http://example.com/path/to/file.txt'}
    >>> get_dataset_filename(ds_dict)
    'file.txt'
    >>> ds_dict['file_name'] = 'new_filename.blob'
    >>> get_dataset_filename(ds_dict)
    'new_filename.blob'
    """

    file_name = ds_dict.get('file_name', None)
    url = ds_dict.get('url', [])
    if file_name is None:
        file_name = url.split("/")[-1]
    return file_name
