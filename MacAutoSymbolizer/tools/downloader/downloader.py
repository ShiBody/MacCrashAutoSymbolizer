from .fast_download import DownloadRequest
import requests
from tqdm import tqdm
import os
import logging

_logger = logging.getLogger('MacAutoSymbolizer')


def download_symbols_archive(download_item: DownloadRequest, chunk_size=1024, basic_token=None):
    try:
        fname = download_item.dest_file
        if os.path.exists(fname):
            return True
        fdir = os.path.dirname(fname)
        if not os.path.exists(fdir):
            _logger.info(f'[{__name__}] creating directory {fdir}')
            os.makedirs(fdir)

        url = download_item.url
        _logger.info(f'Downloading from {url}...')
        header = None
        if basic_token:
            header = {
                "Authorization": f"Basic {basic_token}"
            }
        resp = requests.get(url, headers=header, stream=True)
        if resp.status_code != 200:
            raise Exception(f"Return {resp.status_code}")

        total = int(resp.headers.get('content-length', 0))
        with open(fname, 'wb') as file, tqdm(
                desc=fname,
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            # i = 0
            # percent = 0
            for data in resp.iter_content(chunk_size=chunk_size):
                # i += 1
                size = file.write(data)
                bar.update(size)
                # new_percent = int(100 * i * size / total)
                # if new_percent!= percent:
                #     percent = new_percent + 10
                    # _logger.info(f'{fname} | {percent}%')

    except Exception as e:
        _logger.error(f'[{__name__}] Failure downloading OSX symbols {download_item.dest_file}:{str(e)}')
        return False
    return True

