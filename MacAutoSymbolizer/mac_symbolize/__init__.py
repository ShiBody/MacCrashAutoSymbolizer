from .mac_auto_symbolizer import (
    MacAutoSymbolizer,
    Arch,
    SymbolzedItemProcessor
)
import logging

_logger = logging.getLogger('MacAutoSymbolizer')
logging.basicConfig()
_logger.root.setLevel(logging.NOTSET)


def symbol(
        crash_content: str,
        version: str,
        arch: Arch,
        log_handler: logging.Handler = None,
        result_processor: SymbolzedItemProcessor = None
):
    if log_handler:
        _logger.handlers.clear()
        _logger.addHandler(log_handler)
    symbolizer = MacAutoSymbolizer(result_processor)
    if not symbolizer:
        _logger.error(f'[{__name__}.symbol] symbolizer init failed')
        exit(0)
    return symbolizer.run(crash_content, version, arch)