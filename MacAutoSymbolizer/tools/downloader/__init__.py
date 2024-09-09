import os
from MacAutoSymbolizer.tools.downloader.downloader import (
    download_symbols_archive,
    DownloadRequest
)

from MacAutoSymbolizer.tools.utilities import (
    get_download_full_url,
    get_dst_dir_file
)


def download(version, arch, logger):
    if not version:
        raise Exception(f'[{__name__}.download] No version')
    if not arch:
        raise Exception(f'[{__name__}.download] No arch')

    zip_dir, zip_filename = get_dst_dir_file(version, arch)
    # check if exist unzip downloads
    download_zip_file = os.path.join(zip_dir, zip_filename)
    if os.path.exists(zip_dir):
        zip_dir_files = [f for f in os.listdir(zip_dir) if not f.startswith('.')]
        if zip_dir_files:
            logger.info(f'[{__name__}.download] {version}_{arch} already downloaded.')
            if zip_filename in zip_dir_files:
                return download_zip_file, zip_dir # has zip file
            return None, zip_dir # all zipped
    # start download
    url = get_download_full_url(version, arch)
    for tried_time in range(3):
        logger.info(f'[{__name__}.download] Trying download for the {tried_time + 1} time...')
        download_item = DownloadRequest(url, download_zip_file, version, arch)
        ok = download_symbols_archive(download_item, logger)
        if ok:
            return download_zip_file, zip_dir
    raise Exception(f'[{__name__}.download] Try to download {url} for 3 times and all failed.')