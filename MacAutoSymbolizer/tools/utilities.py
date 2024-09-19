import os.path
import re
import logging
import subprocess
import shutil


from .enums import *
import configparser
Config = configparser.ConfigParser()
ROOT_DIR = os.path.abspath(os.curdir)
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.ini')
if os.path.exists(CONFIG_PATH):
    Config.read(CONFIG_PATH)

__author__  = "Cindy Shi <body1992218@gmail.com>"
__status__  = "production"
__version__ = "1.0"
__date__    = "3 May 2024"


CRASH_THREAD_IDENTIFIERS = 'Crashed Thread:'

DEFAULT_CRASH_IDENTIFIERS = [
    'Incident Identifier:',
    'Hardware Model:',
    'Process:',
    'Path:',
    'Identifier:',
    'Version:',
    'Code Type:',
    'Parent Process:',
    'Date/Time:',
    'OS Version:',
    'Report Version:',
    'Exception Type:',
    'Exception Codes:',
    CRASH_THREAD_IDENTIFIERS
]

ARCH_IDENTIFIER = 'Code Type:'


def read(path):
    if os.path.exists(path):
        Config.read(path)
    else:
        raise Exception(f'Invalid path: {path}')


def version_search(version: str):
    matchObj = re.search(r'(4[4-9].[1-9][0-2]?|43.1[1-2]).0.[0-9]+', version)
    if matchObj:
        return matchObj.group()
    return None


def version_full_match(version: str):
    regex = Config.get('regex', 'version_full_regex')
    if regex:
        match_obj = re.fullmatch(regex, version)
        if match_obj:
            return match_obj.group()
    return None


def stack_block_limit() -> int:
    return Config.getint('constants', 'symbol_thread_count')


def crash_identifiers() -> list:
    identifiers = []
    if Config.has_option('constants', 'crash_identifiers'):
        identifiers += str(Config.get('constants', 'crash_identifiers')).split(', ')
    else:
        return DEFAULT_CRASH_IDENTIFIERS
    if Config.has_option('constants', 'thread_identifier'):
        identifiers.append(Config.get('constants', 'thread_identifier'))
    else:
        identifiers.append(CRASH_THREAD_IDENTIFIERS)
    return identifiers


def thread_identifier() -> str:
    if Config.has_option('constants', 'thread_identifier'):
        return Config.get('constants', 'thread_identifier')
    else:
        return CRASH_THREAD_IDENTIFIERS


def empty_crash_id() -> str:
    return Config.get('constants', 'empty_crash_id')


def binary_name_idx() -> int:
    return Config.getint('constants', 'binary_name_idx')


def address_idx() -> int:
    return Config.getint('constants', 'address_idx')


def load_address_idx() -> int:
    return Config.getint('constants', 'load_address_idx')


def arch_x86_regex() -> str:
    return Config.get('regex', 'arch_x86_regex')


def arch_arm64_regex() -> str:
    return Config.get('regex', 'arch_arm64_regex')


def stack_line_regex() -> str:
    return Config.get('regex', 'stack_line_regex')


def symbolized_line_regex() -> str:
    return Config.get('regex', 'symbolized_line_regex')


def binary_image_regex() -> str:
    return Config.get('regex', 'binary_image_regex')


def thread_start_regex() -> str:
    return Config.get('regex', 'thread_start_regex')


def get_diff_list(listA: list, listB: list) -> list:
    return list(set(listA).difference(set(listB)))


def max_cached_symbol_count() -> int:
    return Config.getint('symbols', 'max_cached_symbol_count')

def word_freq_hash() -> int:
    return Config.getboolean('symbols', 'word_freq_hash')


def get_dst_dir_file(
        version: str, architecture: Arch
) -> tuple[str, str]:
    symbol_dir = Config.get('symbols', 'symbol_dir')
    zipfile = Config.get('symbols', 'symbol_zip')
    return os.path.join(symbol_dir, version, architecture), zipfile


def get_symbol_dir() -> str:
    return Config.get('symbols', 'symbol_dir')


def set_symbol_dir(symbol_dir: str):
    Config.set('symbols', 'symbol_dir', symbol_dir)


def list_unhidden_dir(path: str) -> list[str]:
    if os.path.exists(path):
        return [x for x in os.listdir(path) if not x.startswith('.')]
    return []

def is_debug() -> bool:
    try:
        return Config.getboolean('mode', 'debug')
    except:
        return False

def unzip_file(
        zip_file: str, delete_zip_file: bool = False, tried_times: int = 3
) -> tuple[str, bool, str]:
    dst = ''
    ok = False

    archive_filename = os.path.basename(zip_file)
    ext = os.path.splitext(archive_filename)[1].lower()
    if ext != '.7z' and ext != '.zip':
        return dst, ok, \
            f'Cannot unzip {archive_filename}. File type not supported.'
    cmd = '7z' if ext == '.7z' else 'unzip'
    _, filename_ext = os.path.split(archive_filename)
    filename, _ = os.path.splitext(filename_ext)

    dst = os.path.dirname(zip_file) + '/' + filename + '/'
    if os.path.isdir(dst) and os.listdir(dst):
        ok = True
        if delete_zip_file:
            os.remove(zip_file)
        return dst, ok, \
            f'unzip_symbols_archive: {archive_filename} unzipped already.'

    # Extract the archive
    ext_error = ''
    for tried_time in range(0, tried_times):
        exit_code = subprocess.call([cmd, 'x', '-y', zip_file, '-o' + dst])
        dst_files_count = len(os.listdir(dst))

        if exit_code == 0 and dst_files_count > 0:
            ok = True
            if delete_zip_file:
                os.remove(zip_file)
            return dst, ok, \
                f'unzip_symbols_archive: {archive_filename} unzipped done, includes {dst_files_count} files.'
        else:
            ext_error = exit_code
    return dst, ok, \
        f'Extracting {archive_filename} failed with {ext_error}'


def copy_files(
        src_folder,
        dst_folder,
        rm_tree_dir=False,
        rm_source_dir=True,
        root=True,
        ext=''
):
    # if ext is set, we will recognize it as a file not a directory
    if src_folder == dst_folder and not rm_tree_dir:
        logging.info(f'Same src_folder and dst_folder')
        return

    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
    for file in os.listdir(src_folder):
        # file_type = os.path.splitext(file)[1]
        # file_type = file.split('.')[-1]
        src_full_path = os.path.join(src_folder, file)
        dst_full_path = os.path.join(dst_folder, file)
        is_special_file = file.endswith(ext) if ext else False
        if not is_special_file and os.path.isdir(src_full_path) and rm_tree_dir:
            copy_files(
                src_folder=src_full_path,
                dst_folder=dst_folder,
                root=False,
                rm_source_dir=rm_source_dir,
                rm_tree_dir=rm_tree_dir,
                ext=ext
            )
        else:
            shutil.move(src_full_path, dst_full_path)
    if src_folder != dst_folder and rm_source_dir:
        shutil.rmtree(src_folder, ignore_errors=True)


def version_sort(version: str):
    nums = version.split('.')
    return [int(i) for i in nums]


def get_download_full_url(version: str, arch: Arch) -> str:
    zipfile = Config.get('symbols', 'symbol_zip')
    if arch == Arch.arm:
        return os.path.join(Config.get('symbols', 'url_arm64'), version, zipfile)
    else:
        return os.path.join(Config.get('symbols', 'url_x86'), version, zipfile)


def get_list_chunks(iterable, chunks: int) -> list:
    divided_version_list = []
    for i in range(0, len(iterable), chunks):
        divided_version_list.append(iterable[i:i + chunks])
    return divided_version_list

