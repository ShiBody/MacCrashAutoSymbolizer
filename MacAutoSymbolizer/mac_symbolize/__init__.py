from .mac_auto_symbolizer import (
    MacAutoSymbolizer,
    Arch,
    SymbolzedItemProcessor,
    SymbolizedItem
)
import logging

default_logger = logging.getLogger('MacAutoSymbolizer')
logging.basicConfig()
default_logger.root.setLevel(logging.NOTSET)


def symbol(
        crash_content: str,
        version: str,
        arch: Arch,
        custom_logger = default_logger,
        result_processor: SymbolzedItemProcessor = None
):
    symbolizer = MacAutoSymbolizer(custom_logger, result_processor)
    if not symbolizer:
        custom_logger.error(f'[{__name__}.symbol] symbolizer init failed')
        exit(0)
    return symbolizer.run(crash_content, version, arch)