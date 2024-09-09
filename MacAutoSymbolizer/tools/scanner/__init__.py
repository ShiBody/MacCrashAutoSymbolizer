# Mac Crash Auto Symbolize Toolkit: Scanner
# Author: Cindy Shi <body1992218@gmail.com>
from .scanner import CrashScanner, ImageBinary

_scanner = CrashScanner()


"""
This function is to scan crash lines and got useful infos

Input: a list of crash line strings
Return:        
"""
def scan(crash_lines: list[str]) -> None:
    if not crash_lines:
        raise Exception(f'[{__name__}scanner.scan] No crash lines')
    _scanner.run(crash_lines)


"""
A dict of crash infos in crash file header
    crash_info, 
        {'Code Type:',
        'Crashed Thread:':,
        'Date/Time:', 
        'Exception Codes:':, 
        'Exception Type:':, 
        'OS Version:':,
        'Path:':, 
        'Process:':',
        'Report Version:':, 
        'Version:':}
"""
def crash_info() -> dict:
    return _scanner.crash_info


"""
un-symbolized threads
"""
def stack_blocks() -> list:
    return _scanner.stack_blocks


""" 
arch in crash file
"""
def arch_in_stack():
    return _scanner.arch_in_stack


""" 
version in binary path
"""
def version_in_stack():
    return _scanner.version_in_stack



"""
a list of uuids/image addresses in un-symbolized stack
"""
def keys_in_stack() -> list:
    return _scanner.keys_in_stack

"""
a dict of binary images used in later symbolize flow, 
{image_addr: uuid/'', ...}
"""
def binary_images_in_stack() -> dict:
    return _scanner.binary_images_in_stack


"""
a dict of binary images in binary lines
{image_addr: ImageBinary, ...}
"""
def binary_images_dict() -> dict:
    return _scanner.images_dict