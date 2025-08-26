# crash line format refer to :
# https://developer.apple.com/documentation/Xcode/adding-identifiable-symbol-names-to-a-crash-report
import asyncio
import logging
import re
import time
import os
from MacAutoSymbolizer.src.utilities import (
    Arch,
    crash_identifiers,
    arch_x86_regex,
    arch_arm64_regex,
    stack_line_regex,
    symbolized_line_regex,
    binary_image_regex,
    thread_start_regex,
    version_search,
    binary_with_version,
    diag_line_regex,
    get_atos_tool_path,
    safe_read_file
)
from MacAutoSymbolizer.src.ips_converter import IPSConverter
from enum import Enum
from pydantic import BaseModel
from typing import Any, Literal



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CrashLineType(int, Enum):
    OTHERS = 0
    INFO = 1
    RAW = 2
    BINARY = 3
    THREAD = 4
    SYMBOLED = 5
    BLANK = 6
    DIAG = 7


class ImageBinary(BaseModel):
    uuid: str = ''
    name: str = ''
    loadAddress: str = ''
    name_from_binary: str = ''
    pathToDSYMFile: str = ''
    binaryArc: Arch | None = None

    def path(self):
        if not(self.pathToDSYMFile) or not(self.name):
            return None
        return f"{self.pathToDSYMFile}/Contents/Resources/DWARF/{self.name}"


class ScannedLine(BaseModel):
    idx: int
    type: CrashLineType
    info: list = []
    line: str

    class Config:
        # This ensures subclasses are properly handled
        use_enum_values = True

    def __str__(self):
        return self.line


class TheadLine(ScannedLine):
    type: Literal[CrashLineType.THREAD] = CrashLineType.THREAD
    threadIdx: int = 0
    threadName: str = ''
    crashed: bool = False


# https://developer.apple.com/documentation/xcode/adding-identifiable-symbol-names-to-a-crash-report#Symbolicate-the-crash-report-with-the-command-line
class RawLine(ScannedLine):
    type: 'CrashLineType' = CrashLineType.RAW
    binary: ImageBinary | None = None
    addressesToSymbolicate: str | None = None
    threadID: int = 0
    threadIdx: int = 0
    isSymbolized: bool = False
    symbolizedRes: Any = None
    space1: str = ' '
    space2: str = ' '

    def __str__(self):
        return f'{self.threadIdx}{self.space1}{self.binary.name}{self.space2}{self.addressesToSymbolicate} {self.symbolizedRes}' if self.isSymbolized else self.line

    def cmd_args(self):
        if not self.binary or not self.binary.path() or not self.binary.loadAddress or not self.addressesToSymbolicate:
            return []
        return [get_atos_tool_path(), '-arch', self.binary.binaryArc.value, '-o', self.binary.path(), '-l', self.binary.loadAddress, str(self.addressesToSymbolicate)]


class SymbolizedLine(RawLine):
    type: 'CrashLineType' = CrashLineType.SYMBOLED
    isSymbolized: bool = True


class DiagLine(ScannedLine):
    type: 'CrashLineType' = CrashLineType.DIAG
    binary: ImageBinary | None = None
    addressesToSymbolicate: str | None = None
    diagIdx: int = 0
    isSymbolized: bool = False
    symbolizedRes: Any = None
    prefix: str = ''

    def __str__(self):
        return f'{self.prefix}{self.diagIdx}  {self.symbolizedRes}  ({self.binary.name})  [{self.addressesToSymbolicate}]' if self.isSymbolized else self.line

    def cmd_args(self):
        if not self.binary or not self.binary.path() or not self.binary.loadAddress or not self.addressesToSymbolicate:
            return []
        if self.isSymbolized:
            return []
        return [get_atos_tool_path(), '-arch', self.binary.binaryArc.value, '-o', self.binary.path(), '-l', self.binary.loadAddress,
                str(self.addressesToSymbolicate)]


class ScanResult(BaseModel):
    crash_info: dict
    stack_blocks: list
    version_in_stack: str | None
    images_dict: dict[str, ImageBinary]


def get_arch(line: str) -> Arch:
    if line:
        info = re.findall(arch_x86_regex(), line.lower().rstrip())
        if info:
            return Arch.osx
    info = re.findall(arch_arm64_regex(), line.lower().rstrip())
    if info:
        return Arch.arm
    return None


class CrashScanner:
    def __init__(self):
        self.crash_info = {}
        self.images_dict: dict[str, ImageBinary] = {}
        self.keys_in_stack: list = []
        self.CRASH_IDENTIFIERS = crash_identifiers()
        self.version_in_stack = None
        self.ips_converter = IPSConverter()
        # self.binary_images_in_stack: dict[str, ImageBinary] = {}

    def _reset(self):
        self.crash_info = {}
        self.version_in_stack = None
        self.images_dict: dict = {}
        self.keys_in_stack: list = []
        # self.binary_images_in_stack: dict[str, ImageBinary] = {}


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
    def is_raw_stack_line(crash_line: str):
        match = re.match(
            stack_line_regex(),
            crash_line.rstrip())
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_symboled_line(crash_line: str):
        match = re.search(symbolized_line_regex(), crash_line.rstrip())
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_binary_image_line(crash_line: str):
        match = re.fullmatch(binary_image_regex(), crash_line.rstrip())
        if match:
            return True, match.groups()
        else:
            return False, []

    @staticmethod
    def is_thread_start_line(crash_line: str):
        match = re.search(thread_start_regex(), crash_line.rstrip())
        if match:
            return True, match.groups() + (crash_line,)
        else:
            return False, []

    @staticmethod
    def is_diag_line(crash_line: str):
        match = re.search(diag_line_regex(), crash_line)
        if match:
            return True, match.groups()
        else:
            return False, []

    async def _scan_crash_line(self, crash_line: str, idx: int):
        crash_line = crash_line.replace('\n', '')
        crash_line = crash_line.removeprefix('b\'')
        strip_crash_line = crash_line.strip()
        if not strip_crash_line:
            return ScannedLine(idx=idx, type=CrashLineType.BLANK, line=crash_line)

        ok, thread_info_groups = CrashScanner.is_thread_start_line(strip_crash_line)
        if ok:
            (thread_idx, is_crash_info, _, is_backtrace_info, _) = thread_info_groups
            if is_backtrace_info:
                crashed = True
            elif is_crash_info and str(is_crash_info).lower().find('crashed') >= 0:
                crashed = True
            else:
                crashed = False
            sxx = TheadLine(
                idx=idx,
                type=CrashLineType.THREAD,
                info=thread_info_groups,
                line=strip_crash_line,
                threadIdx=int(thread_idx) if thread_idx else 0,
                crashed=crashed
            )
            return sxx

        ok, key, value = CrashScanner.is_info_line(strip_crash_line, self.CRASH_IDENTIFIERS)
        if ok:
            self.crash_info[key] = value
            return ScannedLine(idx=idx, type=CrashLineType.INFO, info=[(key, value)], line=strip_crash_line)

        ok, stack_groups = CrashScanner.is_raw_stack_line(crash_line)
        if ok:
            (_, thread_idx, space1, image_name, space2, addr_to_symbolicate, load_addr) = stack_groups
            return RawLine(
                idx=idx,
                line=crash_line,
                info=stack_groups,
                type=CrashLineType.RAW,
                binary=ImageBinary(name=image_name, loadAddress=load_addr),
                addressesToSymbolicate=addr_to_symbolicate,
                threadIdx=thread_idx,
                space1=space1,
                space2=space2,
            )
        ok, binary_image_groups = CrashScanner.is_binary_image_line(crash_line)
        if ok:
            if len(binary_image_groups) == 5:
                [load_addr, name_from_binary, arch, uuid, path] = binary_image_groups
                image_name = os.path.basename(path) if path else ''
                if not self.images_dict.get(image_name):
                    binary = ImageBinary(
                        uuid=uuid,
                        name=image_name,
                        loadAddress=load_addr,
                        name_from_binary=name_from_binary,
                        binaryArc=get_arch(arch),
                    )
                    self.images_dict[image_name] = binary

                if str(crash_line).find(binary_with_version()) > 0:
                    version_in_stack = version_search(crash_line)
                    if version_in_stack:
                        self.version_in_stack = version_in_stack
                        self.crash_info['version'] = version_in_stack
            return ScannedLine(idx=idx, type=CrashLineType.BINARY, info=binary_image_groups, line=crash_line)
        ok, symboled_groups = CrashScanner.is_symboled_line(crash_line)
        if ok:
            (_, thread_idx, space1, image_name, space2, addr_to_symbolicate, symbolized_func, _) = symboled_groups
            binary = ImageBinary(name=image_name) if image_name else None
            return SymbolizedLine(
                idx=idx,
                type=CrashLineType.SYMBOLED,
                line=crash_line,
                binary=binary,
                addressesToSymbolicate=addr_to_symbolicate,
                symbolizedRes=symbolized_func,
                threadIdx=thread_idx,
                space1=space1,
                space2=space2,
            )
        ok, diag_groups = CrashScanner.is_diag_line(crash_line)
        if ok:
            (blanks, diag_idx, symbolized_func, image_name, addr_to_symbolicate) = diag_groups
            return DiagLine(
                idx=idx,
                line=crash_line,
                diagIdx=int(diag_idx) if diag_idx else 0,
                binary=ImageBinary(name=image_name) if image_name else None,
                addressesToSymbolicate=addr_to_symbolicate,
                symbolizedRes=symbolized_func,
                isSymbolized=len(str(symbolized_func).strip())>0,
                prefix=blanks or ''
            )
        return ScannedLine(idx=idx, type=CrashLineType.OTHERS, line=crash_line)

    async def scan_crash_async(self, lines: list[str]):
        tasks = [self._scan_crash_line(a_line, idx) for idx, a_line in enumerate(lines)]
        results = await asyncio.gather(*tasks)
        return results

    def _generate_result(self, results: list[ScannedLine]) -> ScanResult:
        stack_blocks = []
        _stack_lines = []

        # generate stack_blocks

        for result in results:
            line_type: CrashLineType = result.type
            if line_type in [CrashLineType.BLANK, CrashLineType.THREAD]:
                if _stack_lines:
                    stack_blocks.append(_stack_lines.copy())
                    _stack_lines.clear()
                if line_type == CrashLineType.THREAD:
                    _stack_lines.append(result)
            elif line_type in [CrashLineType.RAW, CrashLineType.SYMBOLED, CrashLineType.DIAG, CrashLineType.INFO]:
                _stack_lines.append(result)

        if _stack_lines:
            stack_blocks.append(_stack_lines)

        # bring crashed thread to first
        for block in stack_blocks:
            if block:
                line0 = block[0]
                if isinstance(line0, TheadLine) and line0.crashed:
                    # move crashed thread to first
                    if stack_blocks.index(block) != 0:
                        stack_blocks.remove(block)
                        stack_blocks.insert(0, block)
                    break

        res = ScanResult(
            crash_info=self.crash_info or {},
            stack_blocks=stack_blocks or [],
            version_in_stack=self.version_in_stack or '',
            images_dict=self.images_dict or {}
        )
        return res

    def scan_crash(self, content: str | list[str]) -> ScanResult:
        lines = content.splitlines(keepends=True) if isinstance(content, str) else content
        start_code = time.monotonic()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._reset()
            results = loop.run_until_complete(self.scan_crash_async(lines))
            results.sort(key=lambda x: x.idx)
            logger.info(f'[{__name__}.scan_crash] takes {time.monotonic() - start_code} seconds!')
            return self._generate_result(results)
        finally:
            # 确保事件循环被正确关闭，释放资源
            loop.close()

    def scan_diagnostic(self, content: str | list[str]):
        lines = content.splitlines(keepends=True) if isinstance(content, str) else content
        start_code = time.monotonic()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._reset()
            results = loop.run_until_complete(self.scan_crash_async(lines))
            logger.info(f'[{__name__}.scan_crash] takes {time.monotonic() - start_code} seconds!')
            return self._generate_result(results)
        finally:
            # 确保事件循环被正确关闭，释放资源
            loop.close()

    def scan_file(self, file_path: str) -> ScanResult | None:
        """
        :param file_path: a crash file path
        :return:  """
        if not file_path or not os.path.exists(file_path):
            raise Exception(f'File {file_path} does not exist')
        if file_path.endswith('.ips'):
            logger.info(f'[{__name__}.scan_file] is extracting ips file {file_path}...')
            content = self.ips_converter.convert(json_file_path=file_path)
            logger.info(f'[{__name__}.scan_file] is scanning crash file {file_path}...')
            lines = content.splitlines(keepends=False) if isinstance(content, str) else content
            return self.scan_crash(lines)
        elif file_path.endswith('.diag') or file_path.endswith('.spin') or file_path.endswith('.crash'):
            logger.info(f'[{__name__}.scan_file] is extracting diag/spin file {file_path}...')
            content = safe_read_file(file_path)
            return self.scan_diagnostic(content)
            # content = diag_converter.convert_diag_to_text(diag_file_path=file_path)
            # lines = content.splitlines(keepends=False) if isinstance(content, str) else content
            logger.info(f'[{__name__}.scan_file] is scanning diagnostic file {file_path}...')
            # return self.scan_diagnostic(lines)







