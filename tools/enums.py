from enum import Enum


class LineInfo(int, Enum):
    BINARY = 1
    IDX = 2
    ADDRESS = 3


class Arch(str, Enum):
    osx = 'x86_64'
    arm = 'arm64'


class CrashLineType(int, Enum):
    OTHERS = 0
    INFO = 1
    STACK = 2
    BINARY = 3
    THREAD = 4
    SYMBOLED = 5
    BLANK = 6