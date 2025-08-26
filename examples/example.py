from MacAutoSymbolizer import Symbolizer
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def test_content():
    symbolizer = Symbolizer()

    content = """
    46  Foundation                           0x0000000104ce3ed0 Foundation + 1261264
    47  Foundation                           0x0000000104cdfa78 Foundation + 1243768
    48  Foundation                           0x0000000104ce3f74 Foundation + 1261428

    Binary Images:

       0x18d5cb000 -        0x18e21dfff com.apple.Foundation (6.9) <11eb37ae-355b-3a35-af1b-13b599244410> /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation
       0x1a7f7c000 -        0x1a9677fff com.apple.JavaScriptCore (19616) <338fa253-2b8f-3b4c-8adf-665fd7c5e9ef> /System/Library/Frameworks/JavaScriptCore.framework/Versions/A/JavaScriptCore
        """

    result = symbolizer.symbolize(content, "45.10.0.32891", 'arm64')
    for block in result:
        print(f'\n{"-" * 50}\n')
        [print(line) for line in block]

def diag_file_test():
    symbolizer = Symbolizer()
    result = symbolizer.symbolize('examples/crash_files/example.diag', "45.10.0.32870", 'arm64')
    for block in result:
        print(f'\n{"-" * 50}\n')
        [print(line) for line in block]
    # logger.info(f"Symbolization result: {result}")


def ips_file_test():
    symbolizer = Symbolizer()
    # result = symbolizer.symbolize('examples/crash_files/Webex Relay-2025-08-20-145611.ips', "45.10.0.32917", 'arm64', isBackup=True)

    result = symbolizer.symbolize('examples/crash_files/Webex-2025-08-12-113051.ips', "45.10.0.32891", 'arm64')
    for block in result:
        print(f'\n{"-" * 50}\n')
        [print(line) for line in block]
    # logger.info(f"Symbolization result: {result}")


def sentry_file_test():
    symbolizer = Symbolizer()
    # result = symbolizer.symbolize('examples/crash_files/Webex Relay-2025-08-20-145611.ips', "45.10.0.32917", 'arm64', isBackup=True)

    result = symbolizer.symbolize('examples/crash_files/632fc3d32f3c49938876e20244f125df.crash', "45.9.0.32959", 'arm64')
    for block in result:
        print(f'\n{"-" * 50}\n')
        [print(line) for line in block]


if __name__=='__main__':
    # test_content()
    ips_file_test()
    # sentry_file_test()
