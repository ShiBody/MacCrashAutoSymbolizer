import time
import logging
from collections import namedtuple
from multiprocessing import cpu_count, Pool
from .subprocess_atos import SubProcessAtos
from MacAutoSymbolizer.tools.utilities import get_list_chunks

UnSymbolItem = namedtuple("UnSymbolItem", "crash_id app_arch version un_symbol_lines")
SymbolizedItem = namedtuple("SymbolizedItem", "crash_id app_arch version symbolized_lines")


def sub_process(crash_chunk: list[UnSymbolItem]) -> list[SymbolizedItem]:
    res = []
    all_un_symbol_lines = []
    for un_symbol_item in crash_chunk:
        all_un_symbol_lines += un_symbol_item.un_symbol_lines

    process = SubProcessAtos.execute(all_un_symbol_lines)
    if process.result:
        result_dic: dict = process.result
        for un_symbol_item in crash_chunk:
            item_symbolized_lines = []
            for line in un_symbol_item.un_symbol_lines:
                symbolized_line = result_dic.get(line.idx)
                if symbolized_line:
                    item_symbolized_lines.append(symbolized_line)
            res.append(SymbolizedItem(
                un_symbol_item.crash_id,
                un_symbol_item.app_arch,
                un_symbol_item.version,
                item_symbolized_lines
            ))
    return res


def multi_process(crashes: list[UnSymbolItem]) -> list[SymbolizedItem]:
    results = []
    cpu_num = cpu_count()
    crash_chunks = get_list_chunks(crashes, chunks=cpu_num)

    start = time.monotonic()
    with Pool(cpu_num) as pool:
        for a_chunk in crash_chunks:
            pool.apply_async(sub_process, args=a_chunk, callback=results.append)
        pool.close()
        pool.join()
    logging.info(f'Pool takes {time.monotonic() - start} seconds, {len(results)}')
    return results


