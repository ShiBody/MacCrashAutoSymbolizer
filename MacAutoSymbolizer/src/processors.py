
from .multi_process_symbolizer import (
    SymbolizedItem
)

from MacAutoSymbolizer.src.enums import (
    CrashLineType
)

from MacAutoSymbolizer.tools.hash import crash_tag

"""
Examples for symbolizer result processor
"""


def symbolized_item_tostring(item: SymbolizedItem, need_info: bool = True) -> list[str]:
    res = []
    if item:
        if need_info:
            res.append('''
            _FeedbackID_ `{0}`
            _Arch_ `{1}`
            _Version_ `{2}`
            '''.format(
                item.crash_id,
                item.app_arch,
                item.version
            ))
        stack = ""
        for line in item.symbolized_lines:
            # idx return_code useful_output error
            if line.error:
                stack += f'{line.idx} {line.error}\n'
            else:
                stack += f'{line.idx} {line.useful_output}\n'
        res.append("```\n" + stack + "\n```")
    return res

def symbolized_items_tolist(
    items: list[SymbolizedItem],
    stack_blocks: list
) -> list[str]:
    sorted_symbolized_lines = {}
    # extract symbolized items
    for a_item in items:
        for a_line in a_item.symbolized_lines:
            sorted_symbolized_lines[a_line.idx] = a_line.error if a_line.error else a_line.useful_output
    tmp_results = []
    for a_block in stack_blocks:
        # stack_blocks is sorted
        thread_res = []
        stack_line_idx = 0
        for line in a_block:
            line_idx = line[0]
            line_type = line[1]
            line_info = line[2]
            if not line_info:
                continue
            if line_type == CrashLineType.THREAD:
                thread_res.append(str(line_info[-1]))
            elif line_type == CrashLineType.RAW:
                symbolized_res = sorted_symbolized_lines.get(line_idx)
                if symbolized_res:
                    thread_res.append(f'{stack_line_idx}   {symbolized_res}')
                else:
                    thread_res.append(' '.join(line_info))
                stack_line_idx += 1
            elif line_type == CrashLineType.SYMBOLED:
                thread_res.append(str(line_info[0]))
                stack_line_idx += 1
        if thread_res:
            tmp_results += thread_res
    return tmp_results




def symbolized_items_totable(
        items: list[SymbolizedItem],
        stack_blocks: list
):
    results: dict = {
        'title': ['#', 'package', 'address', 'function', 'offset'],
        'rows': [],
        # 'hash': '',
        'tags': []
    }

    def add_a_result(row:list[str]):
        results['rows'].append(row)


    # extract symbolized items
    sorted_symbolized_lines = {}
    for a_item in items:
        for a_line in a_item.symbolized_lines:
            sorted_symbolized_lines[a_line.idx] = a_line.error if a_line.error else a_line.useful_output

    # build results
    packages = []
    functions = []
    for a_block in stack_blocks:
        # stack_blocks is sorted
        for line in a_block:
            line_idx = line[0]
            line_type = line[1]
            line_info = line[2]
            if not line_info:
                continue
            if line_type == CrashLineType.THREAD:
                add_a_result([str(line_info[-1])])
            elif line_type == CrashLineType.RAW:
                symbolized_res = sorted_symbolized_lines.get(line_idx)
                if symbolized_res:
                    packages.append(line_info[1])
                    functions.append(symbolized_res)
                add_a_result([line_info[0], line_info[1], line_info[2], symbolized_res or line_info[3], line_info[4]])
            elif line_type == CrashLineType.SYMBOLED:
                add_a_result(list(line_info[-1]))
    results['tags'] = crash_tag(packages, functions)
    return results

