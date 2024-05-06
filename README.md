## This is a tool for auto-symbolizing Mac crash stack of your app

### Example:
```commandline
symbolize(crash_stack, version, arch)
```
+ crash_stack [string]: un-symbolized crash stack string
+ version [string]: crashed app version
+ arch [Arch]:  `Arch.osx`/`Arch.arm` crashed mac device arch
<br>

### crash stack example:
```
OS Version: macOS 11.7.10 (20G1427)
Report Version: 104

Exception Type: EXC_BAD_ACCESS (SIGBUS)
Exception Codes: BUS_NOOP at 0x0000408778000010
Crashed Thread: 72

Application Specific Information:
XTUM > ZTUM >
Attempted to dereference garbage pointer 0x408778000010.

Thread 72 Crashed:
0   Plugin                          0x107d63c31         0x104dca000 + 199047
1   Plugin                          0x107d63b51         0x104dca000 + 198823
2   Plugin                          0x107d63e78         0x104dca000 + 199630
3   Plugin                          0x107d639d4         0x104dca000 + 198442
4   Plugin                          0x107d63622         0x104dca000 + 197496
5   Plugin                          0x107d63289         0x104dca000 + 196575
6   Plugin                          0x107d314da         0x104dca000 + 1576
7   Plugin                          0x107d3146a         0x104dca000 + 1464
8   Plugin                          0x107d30f7a         0x104dca000 + 200
9   libscf.dylib                    0x1124b70f8         0x11007e000 + 925812
10  libscf.dylib                    0x1124b6407         0x11007e000 + 922499
11  libscf.dylib                    0x1124b6407         0x11007e000 + 922499
12  libscf.dylib                    0x1124b6407         0x11007e000 + 922499
13  libscf.dylib                    0x1124b6ed3         0x11007e000 + 925263
```


### configs:
[regex]
+ version_full_regex: a regex of you app version
+ thread_start_regex: a regex of the thread start line. Thread start line may be like `Thread 72 Crashed:`
+ arch_x86_regex: a regex of x86 arch 
+ arch_arm64_regex: a regex of arm64 arch 

[symbols]
symbol server should be like: http://yoururl/app-version
+ url_x86: x86 symbol download url
+ url_arm64: arm64 symbol download url
+ symbol_dir: directory for downloaded symbols
+ symbol_zip: symbol zip file name
+ max_cached_symbol_count: max cached symbols in symbol_dir. Default is 30.


[constants]
+ symbol_thread_count: the thread count to symbolize. If 2, will only symbol first 2 thread stacks
+ crash_identifiers: crash info identifiers. e.g. `Incident Identifier:, Hardware Model:, Process:, Path:, Identifier:, Version:, Code Type:, Parent Process:, Date/Time:, OS Version:, Report Version:, Exception Type:, Exception Codes:`
+ thread_identifier: prefix in thread start line. e.g. `Crashed Thread:`
+ stack_block_limit: stack block

