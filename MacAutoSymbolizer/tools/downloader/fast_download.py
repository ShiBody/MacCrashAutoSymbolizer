# https://hackernoon.com/how-to-speed-up-file-downloads-with-python

import asyncio
import os.path
import shutil
import logging
import aiofiles
import aiohttp
import time
from tempfile import TemporaryDirectory
from collections import namedtuple

DownloadRequest = namedtuple("FastDownloadRequest", "url dest_file version arch")


async def get_content_length(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as request:
            return request.content_length


def parts_generator(size, start=0, part_size=5 * 1024 ** 2):
    while size - start > part_size:
        yield start, start + part_size
        start += part_size + 1
    yield start, size


async def partial_download(url, headers, save_path, timeout_minutes, logger):
    try:
        async with aiohttp.ClientSession(headers=headers,
                                         timeout=aiohttp.ClientTimeout(total=timeout_minutes * 60)) as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200 and response.status != 206:
                        logging.error(f"server returned {response.status}")
                        return False
                    else:
                        file = await aiofiles.open(save_path, 'wb')
                        await file.write(await response.content.read())
                        await file.close()
                        return True
            except asyncio.TimeoutError:
                message = "Download " + url + " FAILED: asyncio.TimeoutError thrown!"
                logging.error(message)
                return False
    except aiohttp.ClientPayloadError:
        message = "Download " + url + " FAILED: aiohttp.ClientPayloadError thrown!"
        logging.error(message)
        return False


async def process(request: DownloadRequest, timeout_minutes: int, logger=logging):
    # version = request.version
    # arch = request.arch
    dest_file = request.dest_file
    url = request.url

    if os.path.exists(dest_file):
        logging.info(f"Download {url} SUCCESS! Already existed")
        return True, request, ''
    dest_dir = os.path.dirname(dest_file)
    if not os.path.exists(dest_dir):
        logging.info(f"creating directory {dest_dir}")
        os.makedirs(dest_dir)
    logging.info(f"Downloading {url} to {dest_file}")
    filename = os.path.basename(dest_file)
    tmp_dir = TemporaryDirectory(prefix='temp-' + filename + '.', dir=dest_dir)
    size = await get_content_length(url)
    if not size:
        logging.error(f"Download {url} FAILED! Not Found in server.")
        return False, request
    tasks = []
    file_parts = []
    for number, sizes in enumerate(parts_generator(size)):
        part_file_name = os.path.join(tmp_dir.name, f'{filename}.part{number}')
        file_parts.append(part_file_name)
        tasks.append(partial_download(
            url, {'Range': f'bytes={sizes[0]}-{sizes[1]}'}, part_file_name, timeout_minutes, logger))
    partial_results = await asyncio.gather(*tasks)

    if not False in partial_results:
        with open(dest_file, 'wb') as wfd:
            for f in file_parts:
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd)
        logging.info(f"Download {url} SUCCESS.")
        return True, request
    else:
        logging.error(f"Tried to download {url} 3 times but FAILED!")
        return False, request


async def async_download(download_requests: list[DownloadRequest], timeout_minutes: int = 10, logger=logging):
    tasks = [process(request=x, timeout_minutes=timeout_minutes, logger=logger) for x in download_requests]
    results = await asyncio.gather(*tasks)
    return results


def fast_download(
        download_items: list[DownloadRequest],
        timeout_minutes: int = 10,
        logger=logging
):
    start_code = time.monotonic()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(async_download(download_items, timeout_minutes, logger))
    logging.info(f'fast_download.download loop.run {time.monotonic() - start_code} seconds!')
    fails = []
    for result in results:
        if (not result) or len(result) != 2:
            continue
        success = result[0]
        if not success:
            fails.append(result[1])
    download_success = len(fails) == 0
    return download_success, fails


