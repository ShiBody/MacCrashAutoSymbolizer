import requests
from pypdl import Pypdl
from tqdm.asyncio import tqdm
import os
import logging
import asyncio
from collections import namedtuple


DownloadRequest = namedtuple("FastDownloadRequest", "url dest_file version arch")
dl = Pypdl(allow_reuse=False, logger=logging.getLogger("Pypdl"), max_concurrent=1)
_logger = logging.getLogger('MacAutoSymbolizer')


async def async_download_symbols_archive(
        download_item: DownloadRequest,
        basic_token=None
):
    try:
        f_name = download_item.dest_file
        if os.path.exists(f_name):
            return True
        fdir = os.path.dirname(f_name)
        if not os.path.exists(fdir):
            _logger.info(f'[{__name__}] creating directory {fdir}')
            os.makedirs(fdir)

        url = download_item.url
        _logger.info(f'Downloading from {url}...')
        headers = {}
        if basic_token:
            headers["Authorization"] = f"Basic {basic_token}"
        await asyncio.to_thread(
            dl.start,
            url=url,
            file_path=f_name,
            headers=headers,
            retries=3
        )
    except Exception as e:
        _logger.error(f'[{__name__}] Failure downloading OSX symbols {download_item.dest_file}: {str(e)}')
        return False
    return True


def download_symbols_archive(download_item: DownloadRequest, chunk_size=1024, basic_token=None):
    try:
        f_name = download_item.dest_file
        if os.path.exists(f_name):
            return True
        fdir = os.path.dirname(f_name)
        if not os.path.exists(fdir):
            _logger.info(f'[{__name__}] creating directory {fdir}')
            os.makedirs(fdir)

        url = download_item.url
        _logger.info(f'Downloading from {url}...')
        headers = {}
        if basic_token:
            headers["Authorization"] = f"Basic {basic_token}"
        # Using Pypdl for downloading
        dl.start(
            url=url,
            file_path=f_name,
            headers=headers,
            retries=3
        )
        # resp = requests.get(url, headers=header, stream=True)
        # if resp.status_code != 200:
        #     raise Exception(f"Return {resp.status_code}")
        #
        # total = int(resp.headers.get('content-length', 0))
        # with open(f_name, 'wb') as file, tqdm(
        #         desc=f_name,
        #         total=total,
        #         unit='iB',
        #         unit_scale=True,
        #         unit_divisor=1024,
        # ) as bar:
        #     # i = 0
        #     # percent = 0
        #     for data in resp.iter_content(chunk_size=chunk_size):
        #         # i += 1
        #         size = file.write(data)
        #         bar.update(size)
        #         # new_percent = int(100 * i * size / total)
        #         # if new_percent!= percent:
        #         #     percent = new_percent + 10
        #             # _logger.info(f'{f_name} | {percent}%')

    except Exception as e:
        _logger.error(f'[{__name__}] Failure downloading OSX symbols {download_item.dest_file}:{str(e)}')
        return False
    return True

