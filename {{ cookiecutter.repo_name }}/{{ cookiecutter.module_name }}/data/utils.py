import hashlib
import os
import pathlib
import tarfile
import requests
import logging
import shutil
import zipfile
import gzip

from ..paths import interim_data_path, raw_data_path

logger = logging.getLogger(__name__)

hash_function = {
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'md5': hashlib.md5,
}

def get_dataset_filename(ds_dict):
    '''Figure out the downloaded filename for a dataset entry

    if a `file_name` key is present, use this,
    otherwise, use the last component of the `url`
    '''

    file_name = ds_dict.get('file_name', None)
    url = ds_dict.get('url', [])
    if file_name is None:
        file_name = url.split("/")[-1]
    return file_name


def hash_file(fname, algorithm="sha1", block_size=4096):
    '''Compute the hash of an on-disk file

    algorithm: {'md5', sha1', 'sha256'}
        hash algorithm to use
    block_size:
        size of chunks to read when hashing

    Returns:
        Hashlib object
    '''
    hashval = hash_function[algorithm]()
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
    '''
    url_list = kwargs.get('url_list', None)
    if not url_list:
        return fetch_file(force=force, dst_dir=dst_dir, **kwargs)
    result_list = []
    for url_dict in url_list:
        name = url_dict.get('name', 'dataset')
        logger.info(f"Fetching {name}")
        result_list.append(fetch_file(force=force, dst_dir=dst_dir, **url_dict))
    return all([r[0] for r in result_list]), result_list

def fetch_file(url,
               file_name=None, dst_dir=None,
               force=False,
               hash_type="sha1", hash_value=None,
               **kwargs):
    '''Fetch remote files via URL

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


    returns one of:


        (HTTP_Code, downloaded_filename, hash) (if downloaded from URL)
        (True, filename, hash) (if already exists)
        (False, [error])
    if `file_name` already exists, compute the hash of the on-disk file,
    '''
    if dst_dir is None:
        dst_dir = raw_data_path
    if file_name is None:
        file_name = url.split("/")[-1]
    dl_data_path = pathlib.Path(dst_dir)

    if not os.path.exists(dl_data_path):
        os.makedirs(dl_data_path)

    raw_data_file = dl_data_path / file_name

    if raw_data_file.exists():
        raw_file_hash = hash_file(raw_data_file, algorithm=hash_type).hexdigest()
        if hash_value is not None:
            if raw_file_hash == hash_value:
                if force is False:
                    logger.info(f"{file_name} exists and hash is valid")
                    return True, raw_data_file, raw_file_hash
            else:
                logger.warning(f"{file_name} exists but has bad hash {raw_file_hash}."
                               " Re-downloading")
        else:
            if force is False:
                logger.info(f"{file_name} exists, but no hash to check")
                return True, raw_data_file, raw_file_hash

    # Download the file
    try:
        results = requests.get(url)
        results.raise_for_status()
        raw_file_hash = hash_function[hash_type](results.content).hexdigest()
        if hash_value is not None:
            if raw_file_hash != hash_value:
                print(f"Invalid hash on downloaded {file_name}"
                      f" ({hash_type}:{raw_file_hash}) != {hash_type}:{hash_value}")
                return False, None, raw_file_hash
        logger.info(f"Writing {raw_data_file}")
        with open(raw_data_file, "wb") as code:
            code.write(results.content)
    except requests.exceptions.HTTPError as err:
        return False, err, None

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
    if path.endswith('.zip'):
        archive = True
        opener, mode = zipfile.ZipFile, 'r'
    elif path.endswith('.tar.gz') or path.endswith('.tgz'):
        archive = True
        opener, mode = tarfile.open, 'r:gz'
    elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
        archive = True
        opener, mode = tarfile.open, 'r:bz2'
    elif path.endswith('.gz'):
        opener, mode = gzip.open, 'rb'
        outfile, outmode = path[:-3], 'wb'
    else:
        opener, mode = open, 'rb'
        outfile, outmode = path, 'wb'
        logger.info("No compression detected. Copying...")

    with opener(filename, mode) as f_in:
        if archive:
            logger.info(f"Extracting {filename.name}")
            f_in.extractall(path=dst_dir)
        else:
            outfile = pathlib.Path(outfile).name
            logger.info(f"Decompresing {outfile}")
            with open(pathlib.Path(dst_dir) / outfile, outmode) as f_out:
                shutil.copyfileobj(f_in, f_out)

def build_dataset_dict(hash_type='sha1', hash_value=None, url=None,
                       name=None, file_name=None):
    """fetch a URL, return a dataset dictionary entry

    hash_type: {'sha1', 'md5', 'sha256'}
    hash_value: string or None
        if None, hash will be computed from downloaded file
    file_name: string or None
        Name of downloaded file. If None, will be the last component of the URL
    url: URL to fetch

    returns: dict
    """
    fetch_dict = {'url': url, 'hash_type':hash_type, 'hash_value':hash_value, 'name': name, 'file_name':file_name}
    status, path, hash_value = fetch_files(**fetch_dict)
    if status:
        fetch_dict['hash_value'] = hash_value
        return fetch_dict

    raise Exception(f"fetch of {url} returned status: {status}")

def fetch_and_unpack(dataset_name, do_unpack=True):
    '''Fetch and process datasets to their usable form

    dataset_name: string
        Name of dataset. Must be in `datasets.available_datasets`
    do_unpack: boolean
        If false, just download, don't process.

'''
    # This is here to avoid a circular import
    from .datasets import dataset_raw_files
    ds = dataset_raw_files
    if dataset_name not in ds:
        raise Exception(f"Unknown Dataset: {dataset_name}")

    interim_dataset_path = interim_data_path / dataset_name

    logger.info(f"Checking for {dataset_name}")
    if ds[dataset_name].get('url_list', None):
        single_file = False
        status, results = fetch_files(dst_dir=raw_data_path,
                                      **ds[dataset_name])
        if status:
            logger.info(f"Retrieved Dataset successfully")
        else:
            logger.error(f"Failed to retrieve all data files: {results}")
            raise Exception("Failed to retrieve all data files")
        if do_unpack:
            for _, filename, _ in results:
                unpack(filename, dst_dir=interim_dataset_path)
    else:
        single_file = True
        status, filename, hashval = fetch_file(dst_dir=raw_data_path,
                                               **ds[dataset_name])
        hashtype = ds[dataset_name].get('hash_type', None)
        if status:
            logger.info(f"Retrieved Dataset: {dataset_name} "
                        f"({hashtype}: {hashval})")
        else:
            logger.error(f"Unpack to {filename} failed (hash: {hashval}). "
                         f"Status: {status}")
            raise Exception(f"Failed to download raw data: {filename}")
        if do_unpack:
            unpack(filename, dst_dir=interim_dataset_path)
    if do_unpack:
        return interim_dataset_path
    else:
        if single_file:
            return filename
        else:
            return raw_data_path
