import re
from typing import Any
from collections.abc import Callable
from typing_extensions import TypeAlias
from .multi_process_symbolizer import (
    sub_process,
    UnSymbolItem,
    SymbolizedItem
)
from .example_processor import (
    symbolized_items_tolist,
    symbolized_items_totable
)
from .subprocess_atos import UnSymbolLine as UnSymbolLine
from MacAutoSymbolizer.tools.utilities import (
    stack_block_limit,
    address_idx,
    load_address_idx,
    empty_crash_id,
    thread_identifier
)
from MacAutoSymbolizer.tools.enums import (
    CrashLineType
)


def get_crash_id_from_info(info: dict) -> int:
    value = info.get(thread_identifier())
    if not value:
        return -1
    match = re.search(r'([0-9]+)', value)
    if not match:
        return -1
    return int(match.groups()[0])


_ADDRESS_IDX = address_idx()
_EMPTY_CRASH_ID = empty_crash_id()
_LOAD_ADDRESS_IDX = load_address_idx()
_LIMIT = stack_block_limit()


def build_unsymbol_items(
    info: dict,
    stack_blocks: list,
    binary_images_in_stack: dict,
    arch: str,
    version: str,
) -> tuple[list, list]:
    """
    extract full stack into several thread-blocks
    each block is a UnSymbolItem, but they all belong to same crash
    
    :param info:
    :param stack_blocks:
    :param binary_images_in_stack:
    :param arch: 
    :param version: 
    :return: list[UnSymbolItem], stack_blocks
    """
    un_symbol_items = []
    re_stack_blocks = []
    for a_block in stack_blocks:
        un_symbol_lines = []
        is_crash_thread = False
        for x in a_block:
            line_type = x[1]
            if line_type == CrashLineType.THREAD:
                crash_id_from_info = get_crash_id_from_info(info)
                line_info = x[2]
                thread_idx = line_info[0]
                if crash_id_from_info >= 0:
                    is_crash_thread = int(thread_idx) == crash_id_from_info
                else:
                    thread_name = line_info[-1]
                    is_crash_thread = (
                            str(thread_name).startswith('Crash') or str(thread_name).startswith('crash'))
            elif line_type == CrashLineType.STACK:
                idx = x[0]
                line_info = x[2]
                imgAddr = line_info[_LOAD_ADDRESS_IDX]
                address = line_info[_ADDRESS_IDX]
                dyLibPath = binary_images_in_stack.get(imgAddr, None)
                if dyLibPath:
                    un_symbol_lines.append(UnSymbolLine(idx, arch, dyLibPath, imgAddr, address))
        if un_symbol_lines:
            new_item = UnSymbolItem(_EMPTY_CRASH_ID, arch, version, un_symbol_lines)
            if is_crash_thread:
                un_symbol_items.insert(0, new_item)
                re_stack_blocks.insert(0, a_block)
            else:
                un_symbol_items.append(new_item)
                re_stack_blocks.append(a_block)
    if _LIMIT > 0:
        return un_symbol_items[:_LIMIT], re_stack_blocks[:_LIMIT]
    return un_symbol_items, re_stack_blocks


SymbolzedItemProcessor: TypeAlias = Callable[[list[SymbolizedItem], list], Any]  # stable
def process(
        crashes: list[UnSymbolItem],
        stack_blocks: list,
        result_processor:SymbolzedItemProcessor
) -> Any:
    res: list[SymbolizedItem] = sub_process(crashes)
    if res:
        return result_processor(res, stack_blocks)
    else:
        return None