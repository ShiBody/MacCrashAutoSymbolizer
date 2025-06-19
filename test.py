import logging

from MacAutoSymbolizer import (
    symbolize,
    SymbolizedItem,
    Arch,
    async_download_symbol,
    async_symbolize,
    symbolized_item_toMCP
)


logger = logging.getLogger('MacAutoSymbolizer')
logging.basicConfig()
logging.root.setLevel(logging.NOTSET)

class ttt:
    def __init__(self):
        logger.info('init')

    def run(self):
        logger.info('ttt-run')

def test2(t):
    if callable(t.run):
        t.run()


def func():
    raise Exception("func fail")

def test():
    try:
        func()
    except Exception as e:
        logger.error(f'[{__name__}] failed: {str(e)}', exc_info=True)


def test_symbolized_items_totable(
        items: list[SymbolizedItem],
        stack_blocks: list
):
    print('sxx')




if __name__=='__main__':
    logger.info(f'[{__name__}]sxx')
    # crash = ''
    # with open('crash_sentry.txt', 'r') as file:
    #     crash = file.read()
    #
    # title, rest, infos = symbolize(
    #     crash_content=str(crash),
    #     version="44.11.0.30770",
    #     arch=Arch.arm,
    #     result_processor=symbolized_items_totable
    # )

    from MacAutoSymbolizer import async_download_symbol, symbolize
    import asyncio
    version = '45.6.0.32551'
    arch = Arch.arm
    asyncio.run(
        async_download_symbol(
            version=version,
            arch=arch,
        )
    )

    res = asyncio.run(
        async_symbolize(
        crash_content="""
        Thread 9 Crashed:
0   libsystem_pthread.dylib         0x301265364         0x301264000 + 12
1   libc++.1.dylib                  0x3010b5408         0x301096000 + 12
2   libc++.1.dylib                  0x3010b5408         0x301096000 + 12
3   libscf.dylib                    0x30bb9f334         0x308000000 + 36
4   libscf.dylib                    0x30918e4d0         0x308000000 + 792
5   libscf.dylib                    0x30918ffb8         0x308000000 + 2892
6   libscf.dylib                    0x309720820         0x308000000 + 116
7   libscf.dylib                    0x309b3ba7c         0x308000000 + 64
8   libscf.dylib                    0x309b39fc0         0x308000000 + 128
9   libscf.dylib                    0x309b38b04         0x308000000 + 1324
10  libscf.dylib                    0x309b34730         0x308000000 + 2552
11  libscf.dylib                    0x308327908         0x308000000 + 4864
12  libscf.dylib                    0x3091bf6b4         0x308000000 + 82008
13  libscf.dylib                    0x309197fb0         0x308000000 + 248
14  libscf.dylib                    0x309b47c00         0x308000000 + 2192
15  libscf.dylib                    0x309b4b730         0x308000000 + 1840
16  libscf.dylib                    0x308086b50         0x308000000 + 43116
17  libscf.dylib                    0x30858c460         0x308000000 + 7492
18  libscf.dylib                    0x30bc01804         0x308000000 + 1312
19  libscf.dylib                    0x30bc03efc         0x308000000 + 344
20  libsystem_pthread.dylib         0x30126ac08         0x301264000 + 132
        """,
        version=version,
        arch=arch,
        result_processor=symbolized_item_toMCP
    ))

    # download_symbol2(
    #     version="45.8.0.32609",
    #     arch=Arch.arm,
    # )
    print(res)
    print('done!')
