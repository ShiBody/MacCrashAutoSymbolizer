import os, logging
from MacAutoSymbolizer.tools.downloader.downloader import (
    download_symbols_archive,
    DownloadRequest
)

from MacAutoSymbolizer.tools.utilities import (
    get_download_full_url,
    get_dst_dir_file
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
    if not url:
        raise Exception(f'[{__name__}.download] No url_x86/url_arm64 set in config.ini')
    for tried_time in range(3):
        _logger.info(f'[{__name__}.download] Trying download for the {tried_time + 1} time...')
        download_item = DownloadRequest(url, download_zip_file, version, arch)
        ok = download_symbols_archive(download_item)
        if ok:
            return download_zip_file, zip_dir
    raise Exception(f'[{__name__}.download] Try to download {url} for 3 times and all failed.')