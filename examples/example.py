from MacAutoSymbolizer import Symbolizer
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def test_content():
    symbolizer = Symbolizer()

    content = """
    46  UIToolkit                           0x0000000104ce3ed0 UIToolkit + 1261264
47  UIToolkit                           0x0000000104cdfa78 UIToolkit + 1243768
48  UIToolkit                           0x0000000104ce3f74 UIToolkit + 1261428
49  UIToolkit                           0x0000000104ce4994 UIToolkit + 1264020
50  UIToolkit                           0x0000000104cde8ac UIToolkit + 1239212
51  UIToolkit                           0x0000000104d08de4 UIToolkit + 1412580
52  UIToolkit                           0x0000000104d10bb0 UIToolkit + 1444784


Binary Images:
       0x12a6c4000 -        0x12a70bfff com.apple.cmio.DAL.VDC-4 (810.0) <6f4154f0-01b3-3c0b-880d-3c1c6660f302> /System/Library/Frameworks/CoreMediaIO.framework/Versions/A/Resources/VDC.plugin/Contents/MacOS/VDC
       0x100358000 -        0x100363fff libobjc-trampolines.dylib (*) <562f95b3-8118-3d61-a13f-34e819dd863d> /usr/lib/libobjc-trampolines.dylib
       0x160b84000 -        0x167a6bfff Cisco-Systems.Spark.main (45.10.0.32891) <8b9a7903-5cf1-3029-8f5d-daca4281c3cd> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/MacOS/CiscoSparkPlugin
       0x104bb0000 -        0x104e0ffff com.cisco.webex.UIToolkit (1.0) <47466b6a-5ff7-3ae0-bf60-30a0b1345e13> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/UIToolkit.framework/Versions/A/UIToolkit
       0x105748000 -        0x1058b7fff com.airbnb.Lottie (1.0) <83b8d293-bf99-3fb9-9bb6-d7f1169ad7a6> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/Lottie.framework/Versions/A/Lottie
       0x104f30000 -        0x10502bfff io.sentry.Sentry (8.52.1) <4f5776fd-9725-3d55-b90c-d24000f46dd7> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/Sentry.framework/Versions/A/Sentry
       0x102e8c000 -        0x102f9ffff Cisco.appshare (1.0) <e763876f-c9ae-3526-8064-09c42d7ca049> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/appshare.framework/Versions/A/appshare
       0x100388000 -        0x10039ffff com.cisco.AudioDriverHost (1.0) <88e5901f-c7c0-3689-841c-83b7d27cfcd1> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/AudioDriverHost.framework/Versions/A/AudioDriverHost
       0x102d38000 -        0x102dcbfff com.cisco.mediaconverter (20500.2014) <a5e30b7c-2ddf-3bcb-987b-117928ff5813> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/mediaconverter.framework/Versions/A/mediaconverter
       0x100408000 -        0x100413fff www.cisco.wme.PluginInstall (1.0) <cda15656-06a5-3d51-9a60-62c8deea369c> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/PluginInstall.framework/Versions/A/PluginInstall
       0x10549c000 -        0x105667fff com.cisco.wmeclient (20500.2014) <ba43a0ae-aec5-35c4-876d-d48dd7b3fec5> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wmeclient.framework/Versions/A/wmeclient
       0x105fc4000 -        0x1063a3fff com.cisco.MediaSession (20500.2014) <a9ff4ddf-03cf-3d9c-968f-8e175e983408> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/MediaSession.framework/Versions/A/MediaSession
       0x100458000 -        0x100473fff com.cisco.webex.cwsinterface (15.43.0500) <60386ddf-0aa9-38db-8707-b6602aac1e38> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/cwsinterface.framework/Versions/A/cwsinterface
       0x104978000 -        0x104a7ffff libxml2.2.dylib (*) <2b98807d-a508-30ba-a3c7-600ea7a4b49c> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libxml2.2.dylib
       0x104ab4000 -        0x104b37fff libcurl.dylib (*) <9c2c2e81-b364-36d2-bda9-245fb4b42682> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libcurl.dylib
       0x10048c000 -        0x1004affff libnghttp2.dylib (*) <b6832d29-855f-3ef7-9ecf-4276c1d2cf5e> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libnghttp2.dylib
       0x102dfc000 -        0x102e1bfff libcsflogger.dylib (*) <afb3565e-4135-3414-8b99-7d51eb5dd79d> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libcsflogger.dylib
       0x105d88000 -        0x105f53fff libcrypto.dylib (*) <d2f2140b-b85a-3849-b41d-e933107b7337> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libcrypto.dylib
       0x1048b4000 -        0x10490bfff libssl.dylib (*) <7110fcda-51b0-3bd6-939d-ae9a51da2202> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libssl.dylib
       0x1701f4000 -        0x175157fff libscf.dylib (*) <80f4b304-6fe3-38d4-aa16-f4a0c86d4621> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libscf.dylib
       0x106b98000 -        0x107193fff libbwc.dylib (*) <39e2250d-4dac-35a4-ac00-1d1b55e4dd83> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libbwc.dylib
       0x100424000 -        0x100433fff libusb.dylib (*) <2e0a5831-0cd4-346b-83be-c91312652dcc> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libusb.dylib
       0x1004c0000 -        0x1004dbfff libsrtp.dylib (*) <07634fe5-06a6-3e55-ad7b-a39e58a88fb8> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libsrtp.dylib
       0x118d5c000 -        0x1198d7fff libenhanced-callcontrol.dylib (*) <8f236e39-bec3-30b8-80ea-1f946acfaaa4> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libenhanced-callcontrol.dylib
       0x1066a0000 -        0x1068a7fff com.cisco.wseclient (*) <75f6eff3-14ff-31ed-9b15-9a0da2cdf5be> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wseclient.framework/Versions/A/wseclient
       0x106434000 -        0x10654ffff com.cisco.tp (1.0) <532d13fc-c438-3080-98d2-91aa2a282cc0> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/tp.framework/Versions/A/tp
       0x105b58000 -        0x105bbbfff com.cisco.util (1.0) <5a69f72f-3acd-33bb-934e-760a1bf1518f> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/util.framework/Versions/A/util
       0x11c800000 -        0x11cc4bfff com.cisco.wbxaecodec (1.0) <65a98ac2-e4d2-3a8f-a510-2730074e4566> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wbxaecodec.framework/Versions/A/wbxaecodec
       0x118000000 -        0x118293fff com.cisco.wbxaudioengine (3.0) <dd937a75-041c-3c22-9e01-3bfec4be6e3e> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wbxaudioengine.framework/Versions/A/wbxaudioengine
       0x10036c000 -        0x10036ffff com.cisco.wmeutil (1.0) <a6bfe4f8-4787-3259-8abd-85b807037bc1> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wmeutil.framework/Versions/A/wmeutil
       0x105ca0000 -        0x105d2ffff com.cisco.wqos (1.0) <7138650d-b640-3125-82fd-403128a916a5> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wqos.framework/Versions/A/wqos
       0x107300000 -        0x107447fff com.cisco.wrtp (1.0) <3ffc10c1-96ba-387c-903b-66bd7104fb14> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/wrtp.framework/Versions/A/wrtp
       0x105be4000 -        0x105c57fff com.cisco.webex.RootLogger (*) <28dfc750-cbbf-3306-8159-ab1b3954ddb5> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/RootLogger.framework/Versions/A/RootLogger
       0x10483c000 -        0x104863fff com.cisco.webex.ThreadUtilities (*) <38181983-6b63-31a6-bd61-506a4554ff29> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/ThreadUtilities.framework/Versions/A/ThreadUtilities
       0x10492c000 -        0x10494ffff libEncryptedString.dylib (*) <5c27dc80-1af1-3dc1-b2e4-f63fa723e49b> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libEncryptedString.dylib
       0x104b54000 -        0x104b73fff com.cisco.mediastores (1.0) <d0bc0e60-95b9-3587-9b49-efbeb6d2411c> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/mediastores.framework/Versions/A/mediastores
       0x106910000 -        0x1069a3fff libvideoprocess.dylib (*) <7f6ebdc8-a218-32f1-93ee-79d27695f616> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/libvideoprocess.dylib
       0x1003cc000 -        0x1003ebfff com.apple.security.csparser (3.0) <ada5ddea-96d7-3640-9609-e1e3fefe4dba> /System/Library/Frameworks/Security.framework/Versions/A/PlugIns/csparser.bundle/Contents/MacOS/csparser
       0x10033c000 -        0x100347fff cisco.SparkFinder (45.10.0.32891) <f19eedec-c60d-3b50-ac5c-af6523a768fe> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/PlugIns/SparkFinder.bundle/Contents/MacOS/SparkFinder
       0x1000f8000 -        0x100103fff Cisco-Systems.Spark (45.10.0.32891) <a8231c0a-7053-3718-8a07-c2b42d97ba90> /Applications/Webex.app/Contents/MacOS/Webex
       0x18fcbf000 -        0x190fcffff com.apple.AppKit (6.9) <a4e78dd1-6b6e-3f57-924a-4a6a2e679789> /System/Library/Frameworks/AppKit.framework/Versions/C/AppKit
       0x18c0c3000 -        0x18c156873 dyld (*) <ffd8ab66-c9ab-31df-ab80-3a3dff367ddd> /usr/lib/dyld
               0x0 - 0xffffffffffffffff ??? (*) <00000000-0000-0000-0000-000000000000> ???
       0x18c46e000 -        0x18c474ffb libsystem_platform.dylib (*) <e7e2f10a-772a-397f-bd19-a7ea5a54e49f> /usr/lib/system/libsystem_platform.dylib
       0x18c43c000 -        0x18c448ff3 libsystem_pthread.dylib (*) <e4debb6e-421d-33d0-9e17-77ae0e0fe4dc> /usr/lib/system/libsystem_pthread.dylib
       0x18c401000 -        0x18c43bfef libsystem_kernel.dylib (*) <a7d3c07d-0a1e-3c4c-8fba-66905e16bf99> /usr/lib/system/libsystem_kernel.dylib
       0x18c35b000 -        0x18c3e8ff7 libc++.1.dylib (*) <93fbd681-fc78-33a3-affe-568702676142> /usr/lib/libc++.1.dylib
       0x18c2dc000 -        0x18c35aff3 libsystem_c.dylib (*) <1b84a7e4-8958-330c-98b8-27d491dff69e> /usr/lib/system/libsystem_c.dylib
       0x1ffff4000 -        0x20008dfff com.apple.CalendarDaemon (1.0) <0d4e87c0-9114-3cf2-88d0-b316725884f5> /System/Library/PrivateFrameworks/CalendarDaemon.framework/Versions/A/CalendarDaemon
       0x18c4a2000 -        0x18c978fff com.apple.CoreFoundation (6.9) <a68b8c77-1dbd-35b0-83fe-42ad58dd6629> /System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation
       0x18c25b000 -        0x18c291fff libsystem_malloc.dylib (*) <00379936-c90e-3d9d-a569-3f97338f1472> /usr/lib/system/libsystem_malloc.dylib
       0x196775000 -        0x19679efff com.apple.audio.caulk (1.0) <3863bf77-fb9e-3c5f-8790-d879a2bb092a> /System/Library/PrivateFrameworks/caulk.framework/Versions/A/caulk
       0x1a4e0b000 -        0x1a4e2efff com.apple.ANEServices (7.23) <45ea4c9d-1f05-38f8-b090-4f22b79f5154> /System/Library/PrivateFrameworks/ANEServices.framework/Versions/A/ANEServices
       0x1916a5000 -        0x191a75fff com.apple.CFNetwork (1.0) <034d0565-49cb-342f-8e6a-3888b596c736> /System/Library/Frameworks/CFNetwork.framework/Versions/A/CFNetwork
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


if __name__=='__main__':
    test_content()
    # ips_file_test()
