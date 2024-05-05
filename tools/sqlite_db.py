import datetime
import os
import sqlite3
import sys
from sqlite3 import Error
import logging
from typing import Optional


__author__  = "Cindy Shi <body1992218@gmail.com>"
__status__  = "production"
__version__ = "1.0"
__date__    = "3 May 2024"


class SqliteDB:
    @classmethod
    def create(
            cls,
            db_name: str, create_table: str, table_name: str,
            host: Optional[str], user: Optional[str], pwd_environ_key: Optional[str]
    ):
        try:
            if not create_table:
                raise Exception("No create table string.")
            if not table_name:
                raise Exception("No table name.")
            db = cls(db_name, host, user, pwd_environ_key)
            db._table_name = table_name
            db._create_local_db(create_table)
            return db
        except Exception as err:
            logging.error(f'SqliteDB create FAILED: {str(err)}')
            return None

    def __init__(self, db_name: str, host: str, user: str, pwd_environ_key: str = 'SqliteDB_PWD'):
        self._database = db_name
        self._host = host if host else 'localhost'
        self._user = user if user else 'root'
        self._password = os.environ.get(pwd_environ_key)
        if self._password is None:
            self._password = ''

        self._time_format = "%Y-%m-%d %H:%M:%S"
        self._table_name = ''
        self._fields = None

    def _create_local_db(self, create_table: str):
        conn = None
        try:
            conn = sqlite3.connect(self._database)
            cursor = conn.cursor()
            cursor.execute(create_table)
            conn.commit()
            cursor.execute("select * from " + self.table_name)
            self._fields = [description[0] for description in cursor.description]
        except Error as e:
            logging.error(f'create_local_crash_db FAILED: {str(e)}')
        finally:
            if conn:
                conn.close()

    @property
    def table_name(self):
        return self._table_name

    @property
    def fields(self):
        if self._fields is None:
            try:
                conn = sqlite3.connect(self._database)
                cursor = conn.cursor()
                cursor.execute("select * from " + self.table_name)
                self._fields = [description[0] for description in cursor.description]
                conn.close()
            except Exception as err:
                logging.error(f'Get fields FAILED: {str(err)}')
        return self._fields

    @staticmethod
    def _to_insert_value(value):
        if value:
            return str(value)
        else:
            return ''

    def add_data_to_db(self, query_str_list: list[str]) -> int:
        success_cnt = 0
        try:
            if not query_str_list:
                raise Exception("No query_str_list")
            conn = sqlite3.connect(self._database)
            cursor = conn.cursor()
            for query_str in query_str_list:
                cursor.execute(query_str)
                success_cnt += 1
        except Error as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            f_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f'add_data_to_db FAILED: {str(e)} {exc_type} {f_name} {exc_tb.tb_lineno}.')
        finally:
            if conn:
                conn.commit()
                conn.close()
            logging.info(f'Plan to add {len(query_str_list)} data. Finally {success_cnt} added.')
            return success_cnt

    def fetch_data(self, filter_str: Optional[str], *fields):
        conn = sqlite3.connect(self._database)
        if not fields:
            fields = "*"

        query = '''SELECT '''
        query += ",".join(fields)
        query += ''' FROM ''' + self.table_name
        if filter_str:
            query += ''' WHERE ''' + filter_str
        data = []
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            conn.commit()
        except Exception as e:
            logging.error(f'fetch_data FAILED: {str(e)}. fetch string: {query}')
        finally:
            if conn:
                conn.close()
            return data

    def fetch_distinct_value(self, field:str, filter_str: Optional[str]):
        conn = sqlite3.connect(self._database)
        if not field:
            logging.error(f'No field input')

        query = '''SELECT distinct {0} FROM {1}'''.format(field, self.table_name)
        if filter_str:
            query += ''' WHERE ''' + filter_str
        result = None
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            conn.commit()
            if data:
                #only search one result
                result = [i[0] for i in data]
        except Exception as e:
            logging.error(f'fetch_data FAILED: {str(e)}. fetch string: {query}')
        finally:
            if conn:
                conn.close()
            return result

    def clean_data(
            self,
            filter_str: Optional[str],
            time_field:Optional[str] = None,
            time_limit: datetime.timedelta = datetime.timedelta(days=3)
    ) -> bool:
        if filter_str is None and time_field is None:
            logging.error("Please set at least set one param: filter or time_field")
            return False
        conn = None
        result = False
        try:
            conn = sqlite3.connect(self._database)
            cursor = conn.cursor()
            query = '''DELETE FROM ''' + self.table_name + ''' WHERE '''
            if filter_str:
                query += filter_str
            if filter_str and time_field:
                query += ''' AND '''
            if time_field:
                current_time = datetime.datetime.now()
                delete_tolerance = current_time - time_limit
                query += time_field + ''' < "''' + delete_tolerance.isoformat() + '''"'''
            cursor.execute(query)
            conn.commit()
            result = True
        except Error as e:
            logging.error(f'delete data FAILED: {str(e)}. delete string: {query}')
        finally:
            if conn:
                conn.close()
            return result

