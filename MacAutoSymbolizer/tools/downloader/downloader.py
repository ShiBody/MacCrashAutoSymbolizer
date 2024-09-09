from .fast_download import DownloadRequest
import requests
from tqdm import tqdm


def download_symbols_archive(download_item: DownloadRequest, logger, chunk_size=1024):
    try:
        url = download_item.url
        logger.info(f'Downloading from {url}')
        fname = download_item.dest_file
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        with open(fname, 'wb') as file, tqdm(
                desc=fname,
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            i = 0
            percent = 0
            for data in resp.iter_content(chunk_size=chunk_size):
                i += 1
                size = file.write(data)
                new_percent = int(100 * i * size / total)
                if new_percent!= percent:
                    percent = new_percent
                    logger.info(f'{fname} | {percent}%')
                bar.update(size)
    except Exception as e:
        logger.error(f'[{__name__}] Failure downloading OSX symbols {download_item.dest_file}:{str(e)}')
        return False
    return True