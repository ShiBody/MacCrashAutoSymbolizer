from MacAutoSymbolizer.tools.symbolize.subprocess_cmd import SubProcessCmd
from collections import namedtuple
import asyncio
import time

UnSymbolLine = namedtuple("UnSymbolLine", "idx arch dyLibPath imgLoadAddr address")
SymbolizedLine = namedtuple("SymbolizedLine", "idx return_code useful_output error")


class SubProcessAtos:
    @classmethod
    def execute(cls, lines: list[UnSymbolLine], **kwargs):
        process = cls(lines, **kwargs)
        process.result = asyncio.run(process.start())
        # process.result.sort(key=lambda x: x.idx)
        return process

    def __init__(self, symbol_lines: list[UnSymbolLine], **kwargs):
        self._program = 'atos'
        self._symbol_lines = symbol_lines
        self._subprocess_cmd = SubProcessCmd(self._program, **kwargs)
        self.result = None

    async def atos(self, input_line: UnSymbolLine):
        # logging.info(f'{self._program} arch {input_line.arch} -o {input_line.dyLibPath} -l {input_line.imgLoadAddr} {input_line.address}')
        return_code, stdout, stderr = await self._subprocess_cmd.cmd(
            'arch', input_line.arch, '-o', input_line.dyLibPath, '-l', input_line.imgLoadAddr, input_line.address
        )
        useful_output = max(stdout.split('\n'), key=len)
        # SymbolizedLine(input_line.idx, return_code, useful_output, stderr)
        return SubProcessAtos._line_key(input_line), return_code, useful_output, stderr


    @staticmethod
    def _line_key(a_line: UnSymbolLine) -> str:
        return f'{a_line.address}_{a_line.imgLoadAddr}'

    async def start(self):
        line_dict = {}
        unique_symbol_lines = []
        final_res = {}
        for a_line in self._symbol_lines:
            key = SubProcessAtos._line_key(a_line)
            if line_dict.get(key):
                line_dict[key].append(a_line.idx)
            else:
                line_dict[key] = [a_line.idx]
                unique_symbol_lines.append(a_line)
        tasks = [self.atos(x) for x in unique_symbol_lines]
        results = await asyncio.gather(*tasks)
        results_dic = {}
        for r in results:
            results_dic[r[0]] = r[1:]
        for a_line in self._symbol_lines:
            key = SubProcessAtos._line_key(a_line)
            res = results_dic.get(key) #return_code, useful_output, stderr
            if res:
                final_res[a_line.idx] = SymbolizedLine(a_line.idx, res[0], res[1], res[2])
        return final_res




# test
# 'atos',
# 'arch', 'x86_64', '-o', '/Users/xiaoxshi/Desktop/43.12.0.27492/libscf.dylib.dSYM/Contents/Resources/DWARF/libscf.dylib', '-l', '0x1247a1000', '0x12897f479',


if __name__ == '__main__':
    start = time.monotonic()
    my_list = []
    for i in range(0, 10):
        line = UnSymbolLine(i, 'x86_64',
                            '/Users/xiaoxshi/Desktop/43.12.0.27492/libscf.dylib.dSYM/Contents/Resources/DWARF/libscf.dylib',
                            '0x1247a1000', '0x12897f479')
        my_list.append(line)
    my_process = SubProcessAtos.execute(my_list)
    print(f'invoke_async_subprocess takes {time.monotonic() - start} seconds')
    print("sxx end")
