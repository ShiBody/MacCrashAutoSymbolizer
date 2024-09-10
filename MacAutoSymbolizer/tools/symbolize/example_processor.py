from .multi_process_symbolizer import (
    SymbolizedItem
)

from MacAutoSymbolizer.tools.enums import (
    CrashLineType
)

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
            elif line_type == CrashLineType.STACK:
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
        'info': ''
    }

    def add_a_result(
            idx: str = '',
            package: str = '',
            address: str = '',
            function: str = '',
            offset: str = ''
    ):
        results['rows'].append([idx, package, address, function, offset])

    # extract symbolized items
    sorted_symbolized_lines = {}
    for a_item in items:
        for a_line in a_item.symbolized_lines:
            sorted_symbolized_lines[a_line.idx] = a_line.error if a_line.error else a_line.useful_output

    # build results
    for a_block in stack_blocks:
        # stack_blocks is sorted
        stack_line_idx = 0
        for line in a_block:
            line_idx = line[0]
            line_type = line[1]
            line_info = line[2]
            if not line_info:
                continue
            if line_type == CrashLineType.THREAD:
                add_a_result(function=str(line_info[-1]))
            elif line_type == CrashLineType.STACK:
                symbolized_res = sorted_symbolized_lines.get(line_idx)
                add_a_result(line_info[0], line_info[1], line_info[2], symbolized_res, line_info[4])
                stack_line_idx += 1
            elif line_type == CrashLineType.SYMBOLED:
                add_a_result(*line_info[-1])
                stack_line_idx += 1
    return results

