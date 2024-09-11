__author__ = "Cindy Shi <body1992218@gmail.com>"
__status__ = "production"
__version__ = "1.0"
__date__ = "3 May 2024"

import os
import shutil
import asyncio
import uvloop
import logging
from typing import Any

import MacAutoSymbolizer.tools.utilities as utilities
from MacAutoSymbolizer.tools.enums import *
from MacAutoSymbolizer.tools.downloader import download
import MacAutoSymbolizer.tools.scanner as scanner
from MacAutoSymbolizer.tools.libMap import (
    db_lib_paths,
    build_dylib_item,
    delete_dylib_versions,
    store_dylib_items
)
from MacAutoSymbolizer.tools.symbolize import (
    build_unsymbol_items,
    process,
    symbolized_items_tolist,
    SymbolzedItemProcessor
)
from MacAutoSymbolizer.tools.utilities import is_debug

_logger = logging.getLogger('MacAutoSymbolizer')
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class MacAutoSymbolizer:
    def __init__(self, result_processor: SymbolzedItemProcessor=None):
        self._final_version = None
        self._stack_blocks = None
        self._un_symbol_items = None
        self._version = None
        self._symbol_dir = utilities.get_symbol_dir()
        self._dylibs_dir = None
        self._arch = None
        self._lock_file = None
        self._crash_content = None
        self._result_processor = result_processor if result_processor else symbolized_items_tolist

    def __del__(self):
        self._unlock_symbols(self._lock_file)

    def _reset(self):
        self._final_version = None
        self._stack_blocks = None
        self._un_symbol_items = None
        self._version = None
        self._dylibs_dir = None
        self._arch = None
        self._crash_content = None
        # unlock symbol files
        self._unlock_symbols(self._lock_file)
        self._lock_file = None


    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        if not version:
            raise ValueError("Enter version")
        if not utilities.version_full_match(version):
            raise ValueError("Enter valid version match version_full_regex in config.ini")
        self._version = version

    @property
    def arch(self):
        return self._arch

    @arch.setter
    def arch(self, arch):
        if not arch:
            raise ValueError("Enter arch")
        self._arch = arch

    @property
    def crash_content(self):
        return self._crash_content

    @crash_content.setter
    def crash_content(self, content: str):
        if not content:
            raise ValueError("Enter crash_content")
        if not self.arch:
            raise ValueError("Enter arch")
        if not self.version:
            raise ValueError("Enter version")

        self._un_symbol_items, self._stack_blocks = self._scan_content(content)
        if not self._stack_blocks:
            raise ValueError("No crash stack found or no valid images found.")
        self._crash_content = content

    def _scan_content(self, crash_content: str) -> tuple[list, list]:
        """
        :param crash_content: string of crash fragment
        :return: list[UnSymbolItem], stack_blocks
        """
        crash_lines: list[str] = crash_content.split('\n')
        scanner.scan(crash_lines)
        binary_images_in_stack:dict = scanner.binary_images_in_stack() #whose keys are part of binary_images
        if not binary_images_in_stack:
            wiki_link = "https://confluence-eng-gpk2.cisco.com/conf/display/UC/Webex+Supportability+-+Mac+Crash+Handling#WebexSupportabilityMacCrashHandling-Case2:hascrashstacktrace"
            wiki = f'<a href = "{wiki_link}" class ="text-decoration-none">wiki</a>'
            raise Exception(f"No binary image address in stack. Refer format in {wiki}")
        if scanner.version_in_stack():
            self.version = scanner.version_in_stack()
        if scanner.arch_in_stack():
            self.arch = scanner.arch_in_stack()

        keys_need:list = scanner.keys_in_stack()
        paths_from_db:dict = db_lib_paths(self.version, self.arch, keys_need)
        keys_from_db:list = list(paths_from_db.keys())
        to_download:list = utilities.get_diff_list(keys_need, keys_from_db)
        # update binary_images_in_stack, replace uuid with local path
        for addr, uuid in binary_images_in_stack.items():
            # try to find path both by uuid and addr
            path = paths_from_db.get(uuid, None)
            if not path:
                path = paths_from_db.get(addr, None)

            if path:
                binary_images_in_stack[addr] = path
            else:
                binary_images_in_stack[addr] = ''

        # if need download symbols from outer server
        if to_download and self.version:
            zip_file, dst_dir = self._trigger_download()
            if zip_file:
                self._unzip_symbol(zip_file=zip_file, dst_folder=dst_dir)

            # store to lib
            symbols = utilities.list_unhidden_dir(dst_dir)
            store_items = []
            binary_images:dict = scanner.binary_images_dict() # all binary images from input
            for image_addr, an_image in binary_images.items():
                #an_image: namedtuple('ImageBinary', ['uuid', 'name', 'path'])
                image_name = an_image.name
                item_key = an_image.uuid if an_image.uuid else image_addr
                symbol_file = MacAutoSymbolizer._find_symbol(symbols, image_name)
                local_path = MacAutoSymbolizer._get_symbol_inner_path(
                    os.path.join(dst_dir, symbol_file),
                    image_name
                )
                if local_path:
                    # update binary_images_in_stack, replace '' with local path for store items
                    if not binary_images_in_stack.get(image_addr, ''):
                        binary_images_in_stack[image_addr] = local_path
                    store_items.append(build_dylib_item(item_key, self.version, self.arch, local_path))

            if store_items:
                store_dylib_items(store_items)

        _logger.info(f'[{__name__}] dSYM files are ready.')

        return build_unsymbol_items(
            scanner.crash_info(),
            scanner.stack_blocks(),
            binary_images_in_stack,
            self.arch,
            self.version
        )

    @staticmethod
    def _unzip_symbol(
            zip_file: str, dst_folder: str,
    ) -> str:
        if os.path.exists(zip_file):
            try:
                zip_dst, un_zip_ok, msg = utilities.unzip_file(zip_file=zip_file, delete_zip_file=True)
            except Exception as e:
                raise Exception(f'[{__name__}] unzip file {zip_file} failed: {str(e)}')
            if un_zip_ok:
                utilities.copy_files(
                    src_folder=zip_dst,
                    dst_folder=dst_folder,
                    rm_tree_dir=True,
                    ext='.dSYM'
                )
                return zip_dst
            else:
                raise Exception(f'[{__name__}] unzip {zip_file} failed: {msg}')
        else:
            raise Exception(f'[{__name__}] can not find {zip_file}')

    def _trigger_download(self):
        # delete old versions before download
        versions = utilities.list_unhidden_dir(self._symbol_dir)
        max_cached_symbol_count = utilities.max_cached_symbol_count()
        if len(versions) > max_cached_symbol_count:
            versions.sort(key=utilities.version_sort)
            versions_to_remove = []
            length = len(versions) - max_cached_symbol_count
            for version in versions:
                if self._can_delete_version(path = os.path.join(self._symbol_dir, version)):
                    versions_to_remove.append(version)
                    length = length - 1
                if length == 0:
                    break
            for x in versions_to_remove:
                shutil.rmtree(os.path.join(self._symbol_dir, x), ignore_errors=True)
            delete_dylib_versions(versions_to_remove)
        # download
        return download(self.version, self.arch)

    @staticmethod
    def _can_delete_version(path) -> bool:
        if os.path.exists(path):
            files = utilities.list_unhidden_dir(path)
            if not files:
                return True  # empty
            for file in files:
                if os.path.splitext(file)[1] == '.lock':
                    return False
            return True  # not in lock
        return False

    @staticmethod
    def _lock_symbols(version: str):
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

    @staticmethod
    def _unlock_symbols(lock_file):
        if not lock_file:
            return
        if os.path.exists(lock_file):
            os.remove(lock_file)

    @staticmethod
    def _find_symbol(symbols: list[str], image_name: str) -> str:
        for a_symbol in symbols:
            if a_symbol.startswith(image_name.split('.')[0]):
                symbols.remove(a_symbol)
                return a_symbol
        return ''

    @staticmethod
    def _get_symbol_inner_path(symbol_path: str, image_name: str) -> str:
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


    def run(self, crash_content: str, version: str, arch: Arch) -> tuple[str, list[str], Any]:
        results = None
        title = ''
        infos = []
        try:
            self.version = version
            self.arch = arch

            # lock symbol files before do symbolize
            self._lock_file = self._lock_symbols(self.version)

            self.crash_content = crash_content  # crash be scanned and symbol downloaded here

            # do symbolize
            title = f'Crash actual version is [{self.version}_{self.arch}]'
            for key, value in scanner.crash_info().items():
                infos.append(f'{key} {value}')

            results = process(
                self._un_symbol_items,
                self._stack_blocks,
                self._result_processor
            ) if self._un_symbol_items else None

            if not results:
                raise Exception("results is None")
        except Exception as e:
            _logger.error(f'[{__name__}.run] failed: {str(e)}', exc_info=is_debug())
        finally:
            self._reset() # unlock symbol files in reset
            return title, infos, results

