import hashlib
import gzip
import os
import pathlib
import shutil
import tarfile
import zipfile
import zlib
import requests

from .. import paths
from ..log import logger

__all__ = [
    'available_hashes',
    'fetch_file',
    'fetch_files',
    'fetch_text_file',
    'get_dataset_filename',
    'hash_file',
    'infer_filename',
    'unpack',
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
        fetch_action: {'copy', 'message', 'url'}
            Method used to obtain file
        raw_file:
            output file name. If not specified, use the last
            component of the URL

    Examples
    --------
    >>> fetch_files()
    Traceback (most recent call last):
      ...
    Exception: One of `file_name`, `url`, or `source_file` is required
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

def infer_filename(url=None, file_name=None, source_file=None, **kwargs):
    """Infer a filename for a file-to-be-fetched.

    Parameters
    ----------
    file_name: string
        if given, this is returned as the inferred filename (as a string, in case
        if is in pathlib.Path format)
    url: string
        if supplied (and no file_name is specified), the last component of the URL is
        returned as the inferred filename
    source_file: string
        If neither file_name nor url are specified, the last component of the source file
        is returned as the inferred filename.
    """
    if file_name is not None:
        return str(file_name)
    elif url is not None:
        file_name = url.split("/")[-1]
        logger.debug(f"`file_name` not specified. Inferring from URL: {file_name}")
    elif source_file is not None:
        file_name = str(pathlib.Path(source_file).name)
        logger.debug(f"`file_name` not specified. Inferring from `source_file`: {file_name}")
    else:
        raise Exception('One of `file_name`, `url`, or `source_file` is required')


def fetch_file(url=None, contents=None,
               file_name=None, dst_dir=None,
               force=False, source_file=None,
               hash_type="sha1", hash_value=None,
               fetch_action=None, message=None,
               **kwargs):
    '''Fetch the raw files needed by a DataSource.

    A DataSource is usually constructed from one or more raw files.
    This function handles the process of obtaining the raw files.

    Raw files are always specified relative to paths['raw_data_path']

    If `file_name` does not exist, this will attempt to fetch or create
    the file based on the contents of `fetch_action`:
    * message:
        Display `message` to the user and fail. Used when manual intervention
        is required, such as when a licence agreement must be completed.
    * copy:
        Copies the file from somewhere in the filesystem (`source_file`).
        WARNING: This approach rarely leads to a reproducible data workflow
    * url:
        Fetches the source file from `url`
    * create:
        File will be created from the contents of `contents`

    If `file_name` already exists, compute the hash of the on-disk file
    and check

    contents:
        contents of file to be created (if fetch_action == 'create')
    url:
        url to be downloaded
    hash_type:
        Type of hash to compute
    hash_value: (optional)
        if specified, the hash of the downloaded file will be
        checked against this value
    name: (optional)
        Name of this dataset component
    message: string
        Text to be displayed to user (if fetch_action == 'message')
    fetch_action: {'copy', 'message', 'url', 'create'}
        Method used to obtain file
    file_name:
        output file name. If not specified, use the last
        component of the URL
    dst_dir:
        Can be used to override the default raw file location
        (paths['raw_data_path'])
    force: boolean
        normally, the URL is only downloaded if `file_name` is
        not present on the filesystem, or if the existing file has a
        bad hash. If force is True, download is always attempted.
    source_file: path
        Path to source file. (if fetch_action == 'copy')
        Will be copied to `paths['raw_data_path']`

    Returns
    -------
    one of:
        (HTTP_Code, downloaded_filename, hash) (if downloaded from URL)
        (True, filename, hash) (if already exists)
        (False, [error], None)
        (False, `message`, None) (if fetch_action == 'message')

    Examples
    --------
    >>> fetch_file()
    Traceback (most recent call last):
      ...
    Exception: One of `file_name`, `url`, or `source_file` is required
    '''
    _valid_fetch_actions = ('message', 'copy', 'url', 'create')

    # infer filename from url or src_path if needed
    if file_name is None:
        file_name = infer_filename(self, url=url, source_file=source_file)

    if dst_dir is None:
        dst_dir = paths['raw_data_path']
    else:
        dst_dir = pathlib.Path(dst_dir)

    if not dst_dir.exists():
        os.makedirs(dst_dir)

    raw_data_file = dst_dir / file_name

    if fetch_action not in _valid_fetch_actions:
        # infer fetch action (for backwards compatibility)
        if contents is not None:
            fetch_action = 'create'
        elif message is not None:
            fetch_action = 'message'
        elif url is not None:
            fetch_action = 'url'
        elif source_file is not None:
            fetch_action = 'copy'
        logger.debug(f"No `fetch_action` specified. Inferring type: {fetch_action}")

    # If the file is already present, check its hash.
    if raw_data_file.exists():
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        if hash_value is not None:
            if raw_file_hash == hash_value:
                if force is False:
                    logger.debug(f"{file_name} already exists and hash is valid. Skipping download.")
                    return True, raw_data_file, raw_file_hash
            else:  # raw_file_hash != hash_value
                logger.warning(f"{file_name} exists but has bad hash {raw_file_hash}."
                               " Re-fetching.")
        else:  # hash_value is None
            if force is False:
                logger.debug(f"{file_name} exists, but no hash to check. "
                             f"Setting to {hash_type}:{raw_file_hash}")
                return True, raw_data_file, raw_file_hash

    if url is None and contents is None and source_file is None and message is None:
        raise Exception(f"Cannot proceed: {file_name} not found on disk, and no fetch information "
                        "(`url`, `source_file`, `contents` or `message`) specified.")

    if fetch_action == 'url':
        if url is None:
            raise Exception(f"fetch_action = {fetch_action} but `url` unspecified")
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
    elif fetch_action == 'create':
        if contents is None:
            raise Exception(f"fetch_action == 'create' but `contents` unspecified")
        if hash_value is not None:
            logger.warning(f"Hash value ({hash_value}) ignored for fetch_action=='create'")
        with open(raw_data_file, 'w') as fw:
            fw.write(contents)
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        return True, raw_data_file, raw_file_hash
    elif fetch_action == 'copy':
        if source_file is None:
            raise Exception("fetch_action == 'copy' but `copy` unspecified")
        logger.warning(f"Hardcoded paths for fetch_action == 'copy' may not be reproducible. Consider using fetch_action='message' instead")
        shutil.copyfile(source_file, raw_data_file)
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        source_file = pathlib.Path(source_file)
        logger.debug(f"Copying {source_file.name} to raw_data_path")
        return True, raw_data_file, raw_file_hash
    elif fetch_action == 'message':
        if message is None:
            raise Exception("fetch_action == 'copy' but `copy` unspecified")
        print(message)
        return False, message, None
    else:
        raise Exception("No valid fetch_action found: (fetch_action=='{fetch_action}')")

    logger.debug(f'Retrieved {raw_data_file.name} (hash '
                 f'{hash_type}:{raw_file_hash})')
    return results.status_code, raw_data_file, raw_file_hash

def unpack(filename, dst_dir=None, src_dir=None, create_dst=True, unpack_action=None):
    '''Unpack a compressed file

    filename: path
        file to unpack
    dst_dir: path (default paths['interim_data_path'])
        destination directory for the unpack
    src_dir: path (default paths['raw_data_path'])
        destination directory for the unpack
    create_dst: boolean
        create the destination directory if needed
    unpack_action: {'zip', 'tgz', 'tbz2', 'tar', 'gzip', 'compress', 'copy'} or None
        action to take in order to unpack this file. If None, it is inferred.
    '''
    if dst_dir is None:
        dst_dir = paths['interim_data_path']
    if src_dir is None:
        src_dir = paths['raw_data_path']

    if create_dst:
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

    # in case it is a Path
    filename = pathlib.Path(filename)
    path = str((src_dir / filename).resolve())

    if unpack_action is None:
        # infer unpack action
        if path.endswith('.zip'):
            unpack_action = 'zip'
        elif path.endswith('.tar.gz') or path.endswith('.tgz'):
            unpack_action = 'tgz'
        elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
            unpack_action = 'tbz2'
        elif path.endswith('.tar'):
            unpack_action = 'tar'
        elif path.endswith('.gz'):
            unpack_action = 'gz'
        elif path.endswith('.Z'):
            unpack_action = 'compress'
        else:
            logger.warning(f"Can't infer `unpack_action` from filename {filename.name}. Defaulting to 'copy'.")
            unpack_action = 'copy'

    archive = False
    verb = "Copying"
    if unpack_action == 'copy':
        opener, mode = open, 'rb'
        outfile, outmode = path, 'wb'
    elif unpack_action == 'zip':
        archive = True
        verb = "Unzipping"
        opener, mode = zipfile.ZipFile, 'r'
    elif unpack_action == 'tgz':
        archive = True
        verb = "Untarring and ungzipping"
        opener, mode = tarfile.open, 'r:gz'
    elif unpack_action == 'tbz2':
        archive = True
        verb = "Untarring and unbzipping"
        opener, mode = tarfile.open, 'r:bz2'
    elif unpack_action == 'tar':
        archive = True
        verb = "Untarring"
        opener, mode = tarfile.open, 'r'
    elif unpack_action == 'gz':
        verb = "Ungzipping"
        opener, mode = gzip.open, 'rb'
        outfile, outmode = path[:-3], 'wb'
    elif unpack_action == 'compress':
        verb = "Uncompressing"
        logger.warning(".Z files are only supported on systems that ship with gzip. Trying...")
        os.system(f'gzip -f -d {path}')
        opener, mode = open, 'rb'
        path = path[:-2]
        outfile, outmode = path, 'wb'
    else:
        raise Exception(f"Unknown unpack_action: {unpack_action}")

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
