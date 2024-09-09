from .dylib_map import (
    DylibMap,
    DyLibItem,
    DyLibRequest
)

_libMap = DylibMap.create()


def db_lib_paths(version: str, arch: str, uuids: list[str]) -> dict:
    """
    Get a binary local path list filter by input version, arch and uuids
    :param version:
    :param arch:
    :param uuids:
    :return: a dict {uuid: path}
    """
    if not version:
        raise Exception(f'[{__name__}.db_lib_paths] No version')
    if not arch:
        raise Exception(f'[{__name__}.db_lib_paths] No arch')
    if not uuids:
        raise Exception(f'[{__name__}.db_lib_paths] No uuids list')

    requests = [DyLibRequest(uuid, version, arch) for uuid in uuids]
    found = [x for x in _libMap.get_binary_paths(requests=requests) if x[1] == arch]
    paths_in_db = {}
    for a_record in found:
        # example:
        # ('4a11ee94-e929-3165-8f5a-ffcbe855be7b',
        # 'x86_64',
        # './test_symbols/44.11.0.30702/x86_64/CiscoSparkPlugin.bundle.dSYM/Contents/Resources/DWARF/CiscoSparkPlugin')
        uuid = a_record[0]
        path = a_record[2]
        paths_in_db[uuid] = path
    return paths_in_db


"""
 Generate a dylib item that can be stored
"""
def build_dylib_item(uuid: str, version: str, arch: str, inner_path: str):
    if not uuid:
        raise Exception(f'[{__name__}.build_dylib_item] No uuid')
    if not inner_path:
        raise Exception(f'[{__name__}.build_dylib_item] No inner_path for item <{uuid}>')
    if not version:
        raise Exception(f'[{__name__}.build_dylib_item] No version for item <{uuid}>')
    if not arch:
        raise Exception(f'[{__name__}.build_dylib_item] No arch for item <{uuid}>')

    return DyLibItem(uuid, version, arch, inner_path)


"""
 Write dylib items to DB
"""
def store_dylib_items(items: list[DyLibItem]):
    if items:
        _libMap.store_binaries(items)


"""
 Delete all dylib items with input version
"""
def delete_dylib_versions(versions: list[str]):
    if versions:
        _libMap.delete_binaries_by_versions(versions)


