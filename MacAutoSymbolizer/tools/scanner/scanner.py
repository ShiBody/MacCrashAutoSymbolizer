# crash line format refer to :
# https://developer.apple.com/documentation/Xcode/adding-identifiable-symbol-names-to-a-crash-report
import asyncio
import logging
import re
import time
import MacAutoSymbolizer.tools.utilities as utilities
from MacAutoSymbolizer.tools.enums import *
from MacAutoSymbolizer.tools.utilities import ARCH_IDENTIFIER
from collections import namedtuple


ImageBinary = namedtuple('ImageBinary', ['uuid', 'name', 'path'])
CRASH_IDENTIFIERS = utilities.crash_identifiers()
_logger = logging.getLogger('MacAutoSymbolizer')

class CrashScanner:
    def __init__(self):
        self.crash_info = {}
        self.stack_blocks = []
        self.arch_in_stack = None
        self.version_in_stack = None
        self.images_dict: dict = {}
        self.keys_in_stack: list = []
        self.binary_images_in_stack: dict = {}

    def _reset(self):
        self.crash_info = {}
        self.stack_blocks = []
        self.arch_in_stack = None
        self.version_in_stack = None
        self.images_dict: dict = {}
        self.keys_in_stack: list = []
        self.binary_images_in_stack: dict = {}

    @staticmethod
    def get_arch(line: str) -> Arch:
        if line:
            info = re.findall(utilities.arch_x86_regex(), line.lower().rstrip())
        if info:
            return Arch.osx
        info = re.findall(utilities.arch_arm64_regex(), line.lower().rstrip())
        if info:
            return Arch.arm
        return Arch.osx

    @staticmethod
    def is_info_line(crash_line: str, crash_identifiers: list):
        for identifier in crash_identifiers:
            if crash_line.startswith(identifier):
                tmp = crash_line.removeprefix(identifier).removesuffix('\n')
                value = tmp.strip()
                crash_identifiers.remove(identifier)
                return True, identifier, value
        return False, '', ''

    @staticmethod
    def is_stack_line(crash_line: str):
        match = re.match(
            utilities.stack_line_regex(),
            crash_line.rstrip())
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_symboled_line(crash_line: str):
        match = re.search(utilities.symbolized_line_regex(), crash_line.rstrip())
        if match:
            return True, [match.groups()]
        else:
            return False, []

    @staticmethod
    def is_binary_image_line(crash_line: str):
        match = re.fullmatch(utilities.binary_image_regex(), crash_line.rstrip())
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_thread_start_line(crash_line: str):
        match = re.search(utilities.thread_start_regex(), crash_line.rstrip())
        if match:
            return True, match.groups() + (crash_line,)
        else:
            return False, []

    @staticmethod
    async def _scan_line(crash_line: str, idx: int):
        crash_line = crash_line.replace('\n', '')
        crash_line = crash_line.removeprefix('b\'').lstrip(' ')
        crash_line = crash_line.strip()
        # check whether is empty
        if not crash_line:
            return idx, CrashLineType.BLANK, []
        # check whether is info
        ok, key, value = CrashScanner.is_info_line(crash_line, CRASH_IDENTIFIERS)
        if ok:
            return idx, CrashLineType.INFO, [key, value]
        # check whether is thread name
        ok, thread_info_groups = CrashScanner.is_thread_start_line(crash_line)
        if ok:
            return idx, CrashLineType.THREAD, thread_info_groups
        # check whether is thread stack, which needs to be symbolized
        ok, stack_groups = CrashScanner.is_stack_line(crash_line)
        if ok:
            return idx, CrashLineType.STACK, stack_groups
        # check whether is symbolized stack
        ok, symboled_groups = CrashScanner.is_symboled_line(crash_line)
        if ok:
            return idx, CrashLineType.SYMBOLED, symboled_groups
        # check whether is binary image
        ok, binary_image_groups = CrashScanner.is_binary_image_line(crash_line)
        if ok:
            return idx, CrashLineType.BINARY, binary_image_groups

        return idx, CrashLineType.OTHERS, []

    async def _scan_lines(self, lines: list[str]):
        tasks = [self._scan_line(a_line, idx) for idx, a_line in enumerate(lines)]
        results = await asyncio.gather(*tasks)
        return results

    @staticmethod
    def _generate_result(results: list):
        """
        :param results: a result list return from async _scan_lines
        :return:
        crash_info, # a dict of crash infos in crash file header
        stack_blocks, # un-symbolized threads
        arch_in_stack, # arch in crash file
        version_in_stack,  # version in binary path
        images_dict, # a dict of binary images in binary lines, {image_addr: ImageBinary, ...}
        keys_in_stack, # a list of uuids/image addresses in un-symbolized stack
        binary_images_in_stack # a dict of binary images used in later symbolize flow, {image_addr: uuid/'', ...}
        """
        crash_info = {}
        stack_blocks = []
        version_in_stack = None
        images_dict: dict = {}

        keys_in_stack: list = []
        binary_images_in_stack: dict = {}

        # a dict of uuids in binary lines, which will be stored to DB,
        # {uuid: (image_addr, image_name), ...}
        # _uuids_dict: dict = {}
        _stack_lines = []

        # generate crash_info, crash_version, stack_blocks
        results.sort(key=lambda x: x[0])
        for result in results:
            line_type: CrashLineType = result[1]
            if line_type == CrashLineType.OTHERS:
                continue
            elif line_type == CrashLineType.BLANK and _stack_lines:
                stack_blocks.append(_stack_lines.copy())
                _stack_lines.clear()
            elif line_type == CrashLineType.INFO and len(result[2]) == 2:
                line_info: list = result[2]
                crash_info[line_info[0]] = line_info[1]
            elif line_type == CrashLineType.THREAD:
                if _stack_lines:
                    stack_blocks.append(_stack_lines.copy())
                    _stack_lines.clear()
                _stack_lines.append(result)
            elif line_type == CrashLineType.STACK:
                line_info: list = result[2]
                if len(line_info) == 5:
                    image_name = line_info[-4]
                    image_addr = line_info[-2]
                    if not binary_images_in_stack.keys().__contains__(image_addr):
                        binary_images_in_stack[image_addr] = ''
                    if not images_dict.get(image_addr):
                        images_dict[image_addr] = ImageBinary('', image_name, '')
                _stack_lines.append(result)
            elif line_type == CrashLineType.SYMBOLED:
                _stack_lines.append(result)
            elif line_type == CrashLineType.BINARY:
                line_info: list = result[2]
                if len(line_info) == 4:
                    [image_addr, image_name, uuid, app_path] = line_info
                    if images_dict.get(image_addr):
                        image_name = images_dict.get(image_addr).name
                    images_dict[image_addr] = ImageBinary(uuid, image_name, '')
                    if not version_in_stack:
                        version_in_stack = utilities.version_search(app_path)
        if _stack_lines:
            stack_blocks.append(_stack_lines)

        # build keys_in_stack
        for addr in binary_images_in_stack:
            item:ImageBinary = images_dict.get(addr, None)
            if item and item.uuid:
                keys_in_stack.append(item.uuid)
                binary_images_in_stack[addr] = item.uuid
            else:
                keys_in_stack.append(addr)

        # build arch in crash file
        arch_in_stack = crash_info.get(ARCH_IDENTIFIER, None)
        if arch_in_stack:
            arch_in_stack = Arch.osx if str(arch_in_stack).lower().startswith('x86') else Arch.arm

        return crash_info, stack_blocks, arch_in_stack, version_in_stack, images_dict, keys_in_stack, binary_images_in_stack


    def run(self, lines: list[str]):
        """
        :param lines: a list of crash lines
        :return:  """
        start_code = time.monotonic()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reset()
        results = loop.run_until_complete(self._scan_lines(lines))
        _logger.debug(f'[{__name__}] run {time.monotonic() - start_code} seconds!')

        (self.crash_info,
         self.stack_blocks,
         self.arch_in_stack,
         self.version_in_stack,
         self.images_dict,
         self.keys_in_stack,
         self.binary_images_in_stack) = self._generate_result(results)


