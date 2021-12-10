# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.bot_base import State


class Database:
    def __init__(self, database_auth: dict):
        try:
            # Подключение к существующей базе данных
            connection = psycopg2.connect(user=database_auth['user'],
                                          # пароль, который указали при установке PostgreSQL
                                          password=database_auth['password'],
                                          host=database_auth['host'],
                                          port=database_auth['port'])
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            # Курсор для выполнения операций с базой данных
            cursor = connection.cursor()
            sql_create_database = 'create database postgres_db'
            cursor.execute(sql_create_database)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с PostgreSQL закрыто")

    def user_exists(self, vk_id: int) -> bool:
        pass

    def create_user(self, vk_id: int):
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
