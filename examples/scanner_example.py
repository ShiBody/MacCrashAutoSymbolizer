from MacAutoSymbolizer.src.scanner import CrashScanner


if __name__ == '__main__':
    scanner = CrashScanner()

    content = """
    46  Foundation                           0x0000000104ce3ed0 Foundation + 1261264
    47  Foundation                           0x0000000104cdfa78 Foundation + 1243768
    48  Foundation                           0x0000000104ce3f74 Foundation + 1261428

    Binary Images:

       0x18d5cb000 -        0x18e21dfff com.apple.Foundation (6.9) <11eb37ae-355b-3a35-af1b-13b599244410> /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation
       0x1a7f7c000 -        0x1a9677fff com.apple.JavaScriptCore (19616) <338fa253-2b8f-3b4c-8adf-665fd7c5e9ef> /System/Library/Frameworks/JavaScriptCore.framework/Versions/A/JavaScriptCore
        """

    result = scanner.scan_crash(content)
    # result = scanner.scan_file('examples/crash_files/example.diag')
    print(result)