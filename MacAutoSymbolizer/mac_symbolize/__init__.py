from .mac_auto_symbolizer import (
    MacAutoSymbolizer,
    Arch,
    SymbolzedItemProcessor
)
from MacAutoSymbolizer.tools.utilities import unzip_symbol

import logging
import asyncio
# import requests
# class CustomLogHandler(logging.Handler):
#     def __init__(self, host: str, port: int, log_task: Task):
#         logging.Handler.__init__(self)
#         self._url = f'http://{host}:{port}'
#         self._task = log_task
#
#     def emit(self, log_record):
#         # file_name = log_record.name
#         # log_level = log_record.levelname
#         log_message = str(self.format(log_record))
#         result = self._task.delay(log_msg=log_message)
#         # dict_send = {'log_msg': log_message}
#         # self._task.update_state(state="PROGRESS", meta={"log_msg": log_message})
#         # return redirect(url_for("tasks.print_log", log_msg=log_message))
#         with requests.post(f'{self._url}/tasks/result/{result.id}'):
#             print(f"emit log: {log_message}")

_logger = logging.getLogger('MacAutoSymbolizer')
logging.basicConfig()
_logger.root.setLevel(logging.NOTSET)


def symbolize(
        crash_content: str,
        version: str,
        arch: Arch,
        log_handlers: list[logging.Handler] = None,
        result_processor: SymbolzedItemProcessor = None
):
    if log_handlers:
        _logger.handlers = log_handlers
    symbolizer = MacAutoSymbolizer(result_processor)
    if not symbolizer:
        _logger.error(f'[{__name__}.symbol] symbolizer init failed')
        exit(0)
    return symbolizer.run(crash_content.strip(), version, arch)


async def async_symbolize(
        crash_content: str,
        version: str,
        arch: Arch,
        log_handlers: list[logging.Handler] = None,
        result_processor: SymbolzedItemProcessor = None
) -> tuple[str, str, list]:
    if log_handlers:
        _logger.handlers = log_handlers
    symbolizer = MacAutoSymbolizer(result_processor)
    if not symbolizer:
        _logger.error(f'[{__name__}.async_symbolize] symbolizer init failed')
        exit(0)
    return await asyncio.to_thread(
        symbolizer.run,
        crash_content.strip(),
        version,
        arch
    )


from MacAutoSymbolizer.tools.downloader import async_download


async def async_download_symbol(
        version: str,
        arch: Arch,
        log_handlers: list[logging.Handler] = None
) -> bool:
    if log_handlers:
        _logger.handlers = log_handlers
    try:
        download_zip_file, zip_dir = await async_download(version, arch)

        if not zip_dir:
            raise Exception('download_zip_file failed.')
        if download_zip_file:  # None means already unzipped
            await unzip_symbol(download_zip_file, zip_dir)
        return True
    except Exception as e:
        _logger.error(f'[{__name__}.download_symbols] Failed to download symbols for {version} {arch}: {str(e)}', exc_info=True)
        return False


def download_symbol(
        version: str,
        arch: Arch,
        log_handlers: list[logging.Handler] = None
) -> bool:
    if log_handlers:
        _logger.handlers = log_handlers
    from MacAutoSymbolizer.tools.downloader import download
    try:
        download_zip_file, zip_dir = download(version, arch)
        if not zip_dir:
            raise Exception('download_zip_file failed.')
        if download_zip_file: # None means already unzipped
            unzip_symbol(download_zip_file, zip_dir)
        return True
    except Exception as e:
        _logger.error(f'[{__name__}.download_symbols] Failed to download symbols for {version} {arch}: {str(e)}', exc_info=True)
        return False




