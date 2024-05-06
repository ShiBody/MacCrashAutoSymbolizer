import logging
import os
import re
import shutil

import sys
import asyncio
import uvloop
from MacAutoSymbolizer.tools.enums import *
from MacAutoSymbolizer.tools.scanner import CrashScanner
from MacAutoSymbolizer.tools.multi_process_symnolizer import sub_process
from MacAutoSymbolizer.tools.dylib_map import DylibMap, DyLibItem, DyLibRequest
from MacAutoSymbolizer.tools.subprocess_atos import UnSymbolLine as UnSymbolLine
from MacAutoSymbolizer.tools.multi_process_symnolizer import UnSymbolItem as UnSymbolItem
from MacAutoSymbolizer.tools.multi_process_symnolizer import SymbolizedItem as SymbolizedItem
from MacAutoSymbolizer.tools.fast_download import download, FastDownloadRequest
import MacAutoSymbolizer.tools.utilities as utilities

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

__author__ = "Cindy Shi <body1992218@gmail.com>"
__status__ = "production"
__version__ = "1.0"
__date__ = "3 May 2024"

Scanner = CrashScanner()
LibMap = DylibMap.create()


def can_delete_version(
        symbol_dir: str, version: str
) -> bool:
    path = os.path.join(symbol_dir, version)
    if os.path.exists(path):
        files = utilities.list_unhidden_dir(path)
        if not files:
            return True  # empty
        for file in files:
            if os.path.splitext(file)[1] == '.lock':
                return False
        return True  # not in lock
    return False


def remove_useless_symbols(symbol_dir):
    try:
        versions = utilities.list_unhidden_dir(symbol_dir)
        max_cached_symbol_count = utilities.max_cached_symbol_count()
        if len(versions) > max_cached_symbol_count:
            versions.sort(key=utilities.version_sort)
            versions_to_remove = []
            length = len(versions) - max_cached_symbol_count
            for version in versions:
                if can_delete_version(symbol_dir, version):
                    versions_to_remove.append(version)
                    length = length - 1
                if length == 0:
                    break
            for x in versions_to_remove:
                shutil.rmtree(os.path.join(symbol_dir, x), ignore_errors=True)
            if LibMap and versions_to_remove:
                LibMap.delete_binaries_by_version(versions_to_remove)
        else:
            return
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        f_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        message = "{} {} remove_useless_symbols ({}) FAILED: {}".format(exc_type, f_name, exc_tb.tb_lineno, str(e))
        logging.error(message)


def trigger_download(
        version: str, arch: Arch
) -> tuple[bool, str, str]:
    # check if exist unzip downloads
    dst_dir, zipfile = utilities.get_dst_dir_file(version, arch)
    dst = os.path.join(dst_dir, zipfile)
    if os.path.exists(dst_dir):
        parent_files = os.listdir(dst_dir)
        if parent_files:
            logging.info(f'{version} already downloaded.')
            if zipfile in parent_files:
                return True, dst, dst_dir
            return True, "", dst_dir

    # delete old versions before download
    remove_useless_symbols(dst_dir)

    # start download
    url = utilities.get_download_full_url(version, arch)
    for tried_time in range(3):
        download_item = FastDownloadRequest(
            url, dst, version, arch
        )
        ok, need_download_list = download(
            download_items=[download_item],
            logger=logging
        )
        if ok:
            return True, dst, dst_dir
    return False, '', dst_dir


def unzip_symbol(
        zip_file: str, dst_folder: str
) -> str:
    if os.path.exists(zip_file):
        zip_dst, un_zip_ok, msg = utilities.unzip_file(zip_file=zip_file, delete_zip_file=True)
        logging.info(msg)
        if un_zip_ok:
            utilities.copy_files(
                src_folder=zip_dst,
                dst_folder=dst_folder,
                rm_tree_dir=True,
                ext='.dSYM'
            )
            return zip_dst
        else:
            logging.error(f'Cannot unzip file {zip_file}')
    else:
        logging.error(f'Cannot find file {zip_file}')
    return ""


def find_symbol(
        symbols: list[str], image_name: str
) -> str:
    for a_symbol in symbols:
        if a_symbol.startswith(image_name.split('.')[0]):
            symbols.remove(a_symbol)
            return a_symbol
    return ''


def get_symbol_inner_path(
        symbol_path: str, image_name: str
) -> str:
    inner_dir = os.path.join(symbol_path, 'Contents', 'Resources', 'DWARF')
    if not os.path.exists(inner_dir):
        return ''
    inner_files = os.listdir(inner_dir)
    if len(inner_files) == 1:
        return os.path.join(inner_dir, inner_files[0])
    for x in inner_files:
        if image_name.startswith(x):
            return os.path.join(inner_dir, x)
    return ''


def get_crash_id_from_info(info: dict) -> int:
    value = info.get(utilities.thread_identifier())
    if not value:
        return -1
    match = re.search(r'([0-9]+)', value)
    if not match:
        return -1
    return int(match.groups()[0])


def package_symbolized_items(
        items: list[SymbolizedItem],
        stack_blocks: list
) -> list[str]:
    sorted_symbolized_lines = {}
    # extract symbolized items
    for a_item in items:
        for a_line in a_item.symbolized_lines:
            sorted_symbolized_lines[a_line.idx] = a_line.error if a_line.error else a_line.useful_output
    tmp_results = []
    for a_block in stack_blocks:
        # stack_blocks is sorted
        thread_res = []
        stack_line_idx = 0
        for line in a_block:
            line_idx = line[0]
            line_type = line[1]
            line_info = line[2]
            if not line_info:
                continue
            if line_type == CrashLineType.THREAD:
                thread_res.append(str(line_info[-1]))
            elif line_type == CrashLineType.STACK:
                symbolized_res = sorted_symbolized_lines.get(line_idx)
                if symbolized_res:
                    thread_res.append(f'{stack_line_idx}   {symbolized_res}')
                else:
                    thread_res.append(' '.join(line_info))
                stack_line_idx += 1
            elif line_type == CrashLineType.SYMBOLED:
                thread_res.append(str(line_info[0]))
                stack_line_idx += 1
        if thread_res:
            tmp_results += thread_res
    return tmp_results


def scan_content(
        crash_content: str, version: str, arch: str, limit: int = -1
) -> tuple[list, list, str]:
    # extract full stack into several thread-blocks
    # each block is a UnSymbolItem, but they all belong to same crash
    # return list[UnSymbolItem], stack_blocks
    if limit < 0:
        limit = utilities.stack_block_limit()
    load_address_idx = utilities.load_address_idx()
    address_idx = utilities.address_idx()
    empty_crash_id = utilities.empty_crash_id()

    crash_lines: list[str] = crash_content.split('\n')
    info, stack_blocks, content_arch, content_version, load_images = Scanner.scan(crash_lines)
    if not load_images:
        raise Exception(
            "No useful binary image address could be symbolize. \n See crash stacktrace format in wiki: https://confluence-eng-gpk2.cisco.com/conf/display/UC/Webex+Supportability+-+Mac+Crash+Handling#WebexSupportabilityMacCrashHandling-Case2:hascrashstacktrace ")
    version = content_version if content_version else version
    arch = content_arch if content_arch else arch
    addrs = load_images.keys()
    requests = [
        DyLibRequest(
            addr, version, arch
        ) for addr in addrs
    ]
    paths_in_map = [x for x in LibMap.get_binary_paths(requests=requests)
                    if x[1] == arch]
    addrs_found = [x[0] for x in paths_in_map]
    addrs_to_download = utilities.get_diff_list(addrs, addrs_found)
    new_store_items = []
    if addrs_to_download and version:
        ok, zip_file, dst_dir = trigger_download(version, arch)
        if not ok:
            raise Exception(f'Failed to download symbol file of {version} {arch}.')
        if zip_file:
            unzip_symbol(zip_file=zip_file, dst_folder=dst_dir)
        # store to map
        symbols = utilities.list_unhidden_dir(dst_dir)
        for addr in addrs_to_download:
            image_name = load_images[addr][0]  # load_images = {image_addr: [image_name, path], ...}
            symbol_file = find_symbol(symbols, image_name)
            inner_path = get_symbol_inner_path(os.path.join(dst_dir, symbol_file), image_name)
            if inner_path:
                new_store_items.append(DyLibItem(addr, version, arch, inner_path))
        if new_store_items:
            LibMap.store_binaries(new_store_items)
            # return f'Store {len(items)} symbols to map: {version} {arch}'
    logging.info(f'Symbols are ready.')
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
                imgLoadAddr = line_info[load_address_idx]
                address = line_info[address_idx]
                dyLibPath = ''
                if imgLoadAddr in addrs_found:
                    for y in paths_in_map:
                        if imgLoadAddr == y[0]:
                            dyLibPath = y[2]
                            break
                else:
                    for y in new_store_items:
                        if imgLoadAddr == y.binary_addr:
                            dyLibPath = y.path
                if dyLibPath:
                    un_symbol_lines.append(UnSymbolLine(idx, arch, dyLibPath, imgLoadAddr, address))
        if un_symbol_lines:
            new_item = UnSymbolItem(
                empty_crash_id, arch, version, un_symbol_lines
            )
            if is_crash_thread:
                un_symbol_items.insert(0, new_item)
                re_stack_blocks.insert(0, a_block)
            else:
                un_symbol_items.append(new_item)
                re_stack_blocks.append(a_block)
    return un_symbol_items[:limit], re_stack_blocks[:limit], version


def lock_symbols(version: str):
    path = os.path.join(utilities.get_symbol_dir(), version)
    if not os.path.isdir(path):
        return ''
    files = os.listdir(path)
    existed_locks = [int(file.split('.')[0]) for file in files if os.path.splitext(file)[1] == '.lock']
    if not existed_locks:
        new_lock = '1.lock'
    else:
        existed_locks.sort()
        new_lock = f'{existed_locks[-1] + 1}.lock'
    new_lock_file = os.path.join(path, new_lock)
    with open(new_lock_file, 'w'):
        pass
    return new_lock_file


def unlock_symbols(lock_file: str):
    if not lock_file:
        return
    if os.path.exists(lock_file):
        os.remove(lock_file)


def symbolize(
        crash_content: str, version: str, arch: Arch
) -> tuple[str, list[str]]:
    lock_file = ''
    result_stacks = []
    result_title = ''
    try:
        if not utilities.version_full_match(version):
            raise Exception(f'{__name__}._symbolize failed: version input is invalid')
        if not arch:
            raise Exception(f'{__name__}._symbolize failed: arch input is none')
        if not crash_content:
            raise Exception(f'{__name__}._symbolize failed: crash_content input is none')

        un_symbol_items, stack_blocks, final_version = scan_content(
            crash_content=crash_content,
            version=version,
            arch=arch
        )
        if not stack_blocks:
            msg = f'No crash stack found or no valid images found via version {version}.'
            logging.error(f'{__name__}._symbolize failed: {msg}')

        # lock symbol files before do symbolize
        lock_file = lock_symbols(version=final_version)

        # do symbolize
        symbolized_items = sub_process(un_symbol_items)

        # unlock symbol files
        unlock_symbols(lock_file)
        lock_file = ''

        if symbolized_items:
            result_title = f'**Crash Actual Version: {final_version}**'
            result_stacks = package_symbolized_items(symbolized_items, stack_blocks)
        else:
            raise Exception('No symbolized_items.')
    except Exception as e:
        logging.critical(e, exc_info=True)
    finally:
        unlock_symbols(lock_file)
        return result_title, result_stacks