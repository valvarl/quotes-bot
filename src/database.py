# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.methods import State, SearchParams


class Database:
    def __init__(self, database_auth: dict):
        try:
            self.create_database(database_auth=database_auth)
            self.create_tables(database_auth=database_auth)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
            self.close_connection()

    def create_database(self, database_auth: dict):
        # Подключение к существующей базе данных
        self.connection = psycopg2.connect(user=database_auth['user'],
                                           password=database_auth['password'],
                                           host=database_auth['host'],
                                           port=database_auth['port'])
        self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        self.cursor = self.connection.cursor()
        sql_create_database = 'create database if not exists {}'.format(database_auth['database'])
        self.cursor.execute(sql_create_database)
        self.close_connection()

    def create_tables(self, database_auth: dict):
        # Подключение к существующей базе данных
        connection = psycopg2.connect(user=database_auth['user'],
                                      password=database_auth['password'],
                                      host=database_auth['host'],
                                      port=database_auth['port'],
                                      database=database_auth['database'])

        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        # Распечатать сведения о PostgreSQL
        print("Информация о сервере PostgreSQL")
        print(connection.get_dsn_parameters(), "\n")
        # Выполнение SQL-запроса
        cursor.execute("SELECT version();")
        # Получить результат
        record = cursor.fetchone()
        print("Вы подключены к - ", record, "\n")

    def close_connection(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Соединение с PostgreSQL закрыто")

    def user_exists(self, vk_id: int) -> bool:
        pass

    def alias_exists(self, alias: str) -> bool:
        pass

    def create_user(self, vk_id: int, alias: str):
        pass

    def set_user_state(self, vk_id: int, state: State):
        pass

    def get_user_state(self, vk_id: int) -> State:
        pass

    def set_user_alias(self, vk_id: int, alias: str):
        pass

    def create_quote(self, vk_id: int, text: str, *, tags=None, author='', attachments=None, private=False) -> int:
        if tags is None:
            tags = []
        if attachments is None:
            attachments = []
        # return quote_id
        return 12345

    def get_quote(self, quote_id: int) -> dict:
        request_result = {
            'vk_id': 12345,  # vk_id of creator
            'author': None,
            'text': '',
            'tags': [],
            'attachments': '',
            'private': False
        }
        return request_result

    def get_user_quotes(self, vk_id: int) -> list:
        request_result = [12345, 12346]
        return request_result

    def get_quotes_on_random(self, max_amount: int) -> list:
        request_result = [12345, 12346]
        return request_result

    def get_quotes_by_word(self, word_states: list, search_param: SearchParams, max_amount: int) -> list:
        request_result = [12345, 12346]
        return request_result

    def get_quotes_by_tag(self, tags: list, search_param: SearchParams, max_amount: int) -> list:
        request_result = [12345, 12346]
        return request_result
