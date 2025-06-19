import os, logging

from MacAutoSymbolizer.tools.downloader.downloader import (
    download_symbols_archive,
    DownloadRequest,
    async_download_symbols_archive
)

from MacAutoSymbolizer.tools.utilities import (
    get_download_full_url,
    get_dst_dir_file,
    get_download_token,
    get_download_full_url_backup,
    get_download_token_backup
)

downloader_logger = logging.getLogger('MacAutoSymbolizer.tools.downloader.downloader')

# Ensure logger is not overwritten
if not isinstance(downloader_logger, logging.Logger):
    raise TypeError("Logger is not properly initialized")


async def async_download(version, arch):
    # === checks ===
    if not version:
        raise Exception(f'[{__name__}.async_download] No version')
    if not arch:
        raise Exception(f'[{__name__}.async_download] No version')
    zip_dir, zip_filename = get_dst_dir_file(version, arch)
    if not zip_dir:
        raise Exception(f'[{__name__}.async_download] No symbol_dir set in config.ini')
    if not zip_filename:
        raise Exception(f'[{__name__}.async_download] No symbol_zip set in config.ini')
    # Check if the directory already contains downloaded files
    download_zip_file = os.path.join(zip_dir, zip_filename)
    if os.path.exists(zip_dir):
        zip_dir_files = [f for f in os.listdir(zip_dir) if not f.startswith('.')]
        if zip_dir_files:
            downloader_logger.info(f'[{__name__}.async_download] {version}_{arch} already downloaded.')
            if zip_filename in zip_dir_files:
                return download_zip_file, zip_dir  # Has zip file
            return None, zip_dir  # All zipped

    # === start download ===
    urls = {}
    url1 = get_download_full_url(version, arch)
    if url1:
        urls[url1] = get_download_token()
    url2 = get_download_full_url_backup(version, arch)
    if url2:
        urls[url2] = get_download_token_backup()
    for url, token in urls.items():
        download_item = DownloadRequest(url, download_zip_file, version, arch)
        ok = await async_download_symbols_archive(download_item, basic_token=token)
        if ok:
            return download_zip_file, zip_dir
    # failed
    raise Exception(f'[{__name__}.async_download] Try to download from {url1} and {url2} all failed.')


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
            downloader_logger.info(f'[{__name__}.download] {version}_{arch} already downloaded.')
            if zip_filename in zip_dir_files:
                return download_zip_file, zip_dir # has zip file
            return None, zip_dir # all zipped

    # === start download ===
    urls = {}
    url1 = get_download_full_url(version, arch)
    if url1:
        urls[url1] = get_download_token()
    url2 = get_download_full_url_backup(version, arch)
    if url2:
        urls[url2] = get_download_token_backup()
    for url, token in urls.items():
        download_item = DownloadRequest(url, download_zip_file, version, arch)
        ok = download_symbols_archive(download_item, basic_token=token)
        if ok:
            return download_zip_file, zip_dir
    # failed
    raise Exception(f'[{__name__}.download] Try to download from {url1} and {url2} all failed.')
