import os, logging
from MacAutoSymbolizer.tools.downloader.downloader import (
    download_symbols_archive,
    DownloadRequest
)

from MacAutoSymbolizer.tools.utilities import (
    get_download_full_url,
    get_dst_dir_file,
    get_download_token,
    get_download_full_url_backup,
    get_download_token_backup
)

_logger = logging.getLogger('MacAutoSymbolizer')


def download(version, arch):
    if not version:
        raise Exception(f'[{__name__}.download] No version')
    if not arch:
        raise Exception(f'[{__name__}.download] No arch')

    zip_dir, zip_filename = get_dst_dir_file(version, arch)
    if not zip_dir:
        raise Exception(f'[{__name__}.download] No symbol_dir set in config.ini')
    if not zip_filename:
        raise Exception(f'[{__name__}.download] No symbol_zip set in config.ini')
    # check if exist unzip downloads
    download_zip_file = os.path.join(zip_dir, zip_filename)
    if os.path.exists(zip_dir):
        zip_dir_files = [f for f in os.listdir(zip_dir) if not f.startswith('.')]
        if zip_dir_files:
            _logger.info(f'[{__name__}.download] {version}_{arch} already downloaded.')
            if zip_filename in zip_dir_files:
                return download_zip_file, zip_dir # has zip file
            return None, zip_dir # all zipped
    # start download
    url = get_download_full_url(version, arch)
    if url:
        for tried_time in range(3):
            _logger.info(f'[{__name__}.download] Trying download for the {tried_time + 1} time...')
            download_item = DownloadRequest(url, download_zip_file, version, arch)
            ok = download_symbols_archive(download_item, basic_token=get_download_token())
            if ok:
                return download_zip_file, zip_dir
    backup_url = get_download_full_url_backup(version, arch)
    if backup_url:
        for tried_time in range(3, 6):
            _logger.info(f'[{__name__}.download] Trying download for the {tried_time + 1} time...')
            download_item = DownloadRequest(backup_url, download_zip_file, version, arch)
            ok = download_symbols_archive(download_item, basic_token=get_download_token_backup())
            if ok:
                return download_zip_file, zip_dir

    raise Exception(f'[{__name__}.download] Try to download {url} and {backup_url} all failed.')
