# crash line format refer to :
# https://developer.apple.com/documentation/Xcode/adding-identifiable-symbol-names-to-a-crash-report
import asyncio
import logging
import re
import time
import tools.utilities as utilities
from tools.enums import *


CRASH_IDENTIFIERS = utilities.crash_identifiers()


class CrashScanner:
    def __init__(self):
        self._reset()

    def _reset(self):
        self._crash_info = {}
        self._binary_image = {}
        self._crash_lines = []
        self._crash_version = ''

    @staticmethod
    def get_arch(line: str) -> Arch:
        if line:
            info = re.findall(utilities.arch_x86_regex(), line.lower())
        if info:
            return Arch.osx
        info = re.findall(utilities.arch_arm64_regex(), line.lower())
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
        match = re.fullmatch(
            utilities.stack_line_regex(),
            crash_line)
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_symboled_line(crash_line: str):
        match = re.search(utilities.symbolized_line_regex(), crash_line)
        if match:
            return True, [crash_line]
        else:
            return False, []

    @staticmethod
    def is_binary_image_line(crash_line: str):
        match = re.fullmatch(utilities.binary_image_regex(), crash_line)
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_thread_start_line(crash_line: str):
        match = re.search(utilities.thread_start_regex(), crash_line)
        if match:
            return True, match.groups() + (crash_line,)
        else:
            return False, []

    @staticmethod
    async def _scan_line(crash_line: str, idx: int):
        crash_line = crash_line.replace('\n', '')
        crash_line = crash_line.removeprefix('b\'').lstrip(' ')
        # check whether is empty
        if not crash_line.strip():
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
        crash_info = {}
        arch = ''
        crash_version = ''
        binary_images = {}
        useful_binary_images = {}  # {image_addr: [image_name, path], ...}
        stack_blocks = []
        stack_lines = []
        results.sort(key=lambda x: x[0])
        for result in results:
            line_type: CrashLineType = result[1]
            if line_type == CrashLineType.OTHERS:
                continue
            elif line_type == CrashLineType.BLANK and stack_lines:
                stack_blocks.append(stack_lines.copy())
                stack_lines.clear()
            elif line_type == CrashLineType.INFO and len(result[2]) == 2:
                line_info: list = result[2]
                crash_info[line_info[0]] = line_info[1]
            elif line_type == CrashLineType.THREAD:
                if stack_lines:
                    stack_blocks.append(stack_lines.copy())
                    stack_lines.clear()
                stack_lines.append(result)
            elif line_type == CrashLineType.STACK:
                line_info: list = result[2]
                if line_info[-4:]:
                    useful_binary_name = line_info[-4]
                    useful_binary_addr = line_info[-2]
                    useful_binary_images[useful_binary_addr] = [useful_binary_name]
                stack_lines.append(result)
            elif line_type == CrashLineType.SYMBOLED:
                stack_lines.append(result)
            elif line_type == CrashLineType.BINARY:
                line_info: list = result[2]
                if len(line_info) == 3:
                    binary_images[line_info[0]] = [line_info[1], line_info[2]]
                    if not crash_version:
                        crash_version = utilities.version_search(line_info[2])
        if stack_lines:
            stack_blocks.append(stack_lines)
        for addr in useful_binary_images:
            a_path = binary_images[addr] if binary_images.get(addr) else ''
            useful_binary_images[addr].append(a_path)
        return crash_info, stack_blocks, arch, crash_version, useful_binary_images

    def scan(self, lines: list[str]):
        start_code = time.monotonic()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reset()
        results = loop.run_until_complete(self._scan_lines(lines))
        logging.info(f'scanner.scan loop.run {time.monotonic() - start_code} seconds!')
        res = self._generate_result(results)
        return res


if __name__ == '__main__':
    with open('../../../tests/manual_symbol_job/test_crash_content', 'r') as f:
        lines = f.readlines()
        my = CrashScanner()
        sxx = my.scan(lines)
        print('sxx')
