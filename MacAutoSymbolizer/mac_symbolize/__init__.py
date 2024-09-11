from .mac_auto_symbolizer import (
    MacAutoSymbolizer,
    Arch,
    SymbolzedItemProcessor
)
import logging

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
    return symbolizer.run(crash_content, version, arch)