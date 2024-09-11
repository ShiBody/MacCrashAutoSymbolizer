import logging

from MacAutoSymbolizer import (
    symbolize,
    SymbolizedItem,
    symbolized_items_totable,
Arch
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
    crash = ''
    with open('crash_example.txt', 'r') as file:
        crash = file.read()

    title, rest = symbolize(
        crash_content=str(crash),
        version="44.11.0.30702",
        arch=Arch.osx,
        result_processor=symbolized_items_totable
    )

    print('done!')
