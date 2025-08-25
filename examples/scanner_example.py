from MacAutoSymbolizer.src.scanner import CrashScanner


if __name__ == '__main__':
    scanner = CrashScanner()

    content = """
Thread 65:: JavaScriptCore libpas scavenger
0   libsystem_kernel.dylib         0x000043cc __psynch_cvwait + 8
1   libsystem_pthread.dylib        0x000070e0 _pthread_cond_wait + 984
2   JavaScriptCore                 0x016f7960 scavenger_thread_main + 1584
3   libsystem_pthread.dylib        0x00006c0c _pthread_start + 136
4   libsystem_pthread.dylib        0x00001b80 thread_start + 8

Binary Images:
     0x10478c000 -      0x104797fff Cisco-Systems.Spark (45.8.0.32653) <0cf04ff7-a8a7-3e9c-8dcf-c7bd3daf34a6> /Applications/Webex.app/Contents/MacOS/Webex
     0x10897c000 -      0x108987fff cisco.SparkFinder (45.8.0.32653) <8138df8e-689f-3c10-b5e3-8c6c16104a6b> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/PlugIns/SparkFinder.bundle/Contents/MacOS/SparkFinder
     0x108a04000 -      0x108a23fff com.apple.security.csparser (3.0) <3a905673-ada9-3c57-992e-b83f555baa61> /System/Library/Frameworks/Security.framework/Versions/A/PlugIns/csparser.bundle/Contents/MacOS/csparser
     0x308b58000 -      0x30fa17fff Cisco-Systems.Spark.main (45.10.0.32958) <4f2ec3bb-eaaf-335e-856e-76726099986c> /Users/USER/Library/Application Support/Cisco Spark/*/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/MacOS/CiscoSparkPlugin
     0x109800000 -      0x109a63fff com.cisco.webex.UIToolkit (45) <d773599f-671f-332c-a8fc-08918973b468> /Users/USER/Library/Application Support/Cisco Spark/*/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/UIToolkit.framework/Versions/A/UIToolkit
     0x108a40000 -      0x108baffff com.airbnb.Lottie (1.0) <83b8d293-bf99-3fb9-9bb6-d7f1169ad7a6> /Users/USER/Library/Application Support/Cisco Spark/*/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/Lottie.framework/Versions/A/Lottie

        """

    result = scanner.scan_crash(content)
    # result = scanner.scan_file('examples/crash_files/example.diag')
    print(result)