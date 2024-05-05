from tools.sqlite_db import SqliteDB
from tools.utilities import version_sort
from collections import namedtuple
from typing import Optional
import logging

DyLibRequest= namedtuple("DyLibRequest", "binary_addr version arch")
DyLibItem = namedtuple("DyLibItem", "binary_addr version arch path")
VERSION_LIMIT = 50  # max versions stored


class DylibMap:
    @classmethod
    def create(cls):
        db_name = "DylibMap"
        table_name = "mapTable"
        db = SqliteDB.create(
            db_name=db_name,
            create_table=cls.create_table(table_name),
            table_name=table_name,
            host='', user='', pwd_environ_key=''
        )
        return cls(db, db_name, table_name)

    def __init__(self, database: SqliteDB, db_name: str, table_name: str):
        self._map_db = database
        self._db_name = db_name
        self._table_name = table_name

    @property
    def db_name(self):
        return self._db_name

    @property
    def table_name(self):
        return self._table_name

    @staticmethod
    def create_table(table_name:str):
        if not table_name:
            return ''
        return '''CREATE TABLE IF NOT EXISTS ''' + table_name + ''' (
                map_key TEXT NOT NULL,
                arch TEXT NOT NULL,
                version TEXT NOT NULL,
                path TEXT NOT NULL,
                PRIMARY KEY (map_key, arch)
            );'''

    @property
    def database(self):
        return self._map_db

    def stored_version_list(self, filter_versions: list[str] = []) -> list[str]:
        if filter_versions:
            filter_string = " OR ".join(["version LIKE '" + x + "%'" for x in filter_versions])
        else:
            filter_string = ""
        versions = self.database.fetch_distinct_value(
            field="version",
            filter_str=filter_string
        )
        if versions:
            versions.sort(key=version_sort)
        return versions

    def _add_query_str(self, item: DyLibItem) -> str:
        return '''INSERT INTO `{0}` (
                    `map_key`,
                    `arch`,
                    `version`,
                    `path`
                ) VALUES (
                    "{1}",
                    "{2}",
                    "{3}",
                    "{4}"
                );'''.format(
            self.table_name,
            item.binary_addr,
            item.arch,
            item.version,
            item.path
        )

    def get_binary_path(self, a_request: DyLibRequest) -> str:
        if not a_request or self.database is None:
            logging.error('No request or no database')
            return ''
        filter_str = '''map_key="''' + a_request.binary_addr + \
                     '''" AND arch="''' + str(a_request.arch) + '''"'''
        res = self.database.fetch_data(filter_str, 'path')
        return res if res else ''

    def get_binary_paths(self, requests: list[DyLibRequest]) -> list:
        if not requests or self.database is None:
            logging.error('Empty requests or no database')
            return []
        filter_str = "map_key IN ('" + "', '".join([x.binary_addr for x in requests]) + "')"
        res = self.database.fetch_data(filter_str, 'map_key', 'arch', 'path')
        return res if res else []

    def store_binary(self, item: DyLibItem) -> bool:
        if not item or self.database is None:
            logging.error('No item or no database')
            return False
        add_str = self._add_query_str(item)
        return self.database.add_data_to_db(
            query_str_list=[add_str]
        ) > 0

    def store_binaries(self, items:list[DyLibItem]) -> int:
        if not items or self.database is None:
            logging.error('Empty items or no database')
            return 0
        return self.database.add_data_to_db(
            query_str_list=[self._add_query_str(x) for x in items]
        )

    def delete_binaries_by_version(self, version_list: Optional[list[str]]) -> bool:
        versions_to_delete = self.stored_version_list(version_list)
        if not versions_to_delete:
            logging.error('No version to delete.')
            return True
        stored_version_list = self.stored_version_list()
        remaining_count = len(set(stored_version_list) - set(versions_to_delete))
        if remaining_count > VERSION_LIMIT:
            versions_to_delete += stored_version_list[:(remaining_count - VERSION_LIMIT)]
        filter_str = "version IN ('" + "', '".join(versions_to_delete) + "')"
        result = self.database.clean_data(filter_str)
        logging.info(f'Delete version {result} : {versions_to_delete}')
        return result


#test
if __name__ == '__main__':
    my = DylibMap.create()
    # my.store_binary(DyLibItem('test_addr1', '43.9.0.23455', 'arm64', 'test/path'))
    # my.store_binary(DyLibItem('test_addr1', '43.9.0.23455', 'x86_64', 'test/path1'))
    # my.store_binary(DyLibItem('test_addr2', '43.9.0.23455', 'arm64', 'test/path2'))
    # my.store_binary(DyLibItem('test_addr3', '43.9.0.23455', 'arm64', 'test/path3'))
    items = []
    requests = []
    for i in range(0, 10):
        items.append(DyLibItem('addr'+str(i), '43.11.0.1234'+str(i), 'x86_64', 'test/path'+str(i)))
        requests.append(DyLibRequest('addr'+str(i), '43.11.0.1234'+str(i), 'x86_64'))
    my.store_binaries(items)
    res = my.get_binary_paths(requests)
    keys = [x[0] for x in res]
    print('sxx')
    # my.delete_binaries_by_version(['43.10', '43.1'])






