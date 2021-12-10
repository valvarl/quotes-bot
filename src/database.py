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
        self.cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{}'".format(database_auth['database']))
        exists = self.cursor.fetchone()
        if not exists:
            self.cursor.execute('CREATE DATABASE {}'.format(database_auth['database']))
        self.close_connection()

    def create_tables(self, database_auth: dict):
        # Подключение к существующей базе данных
        self.connection = psycopg2.connect(user=database_auth['user'],
                                           password=database_auth['password'],
                                           host=database_auth['host'],
                                           port=database_auth['port'],
                                           database=database_auth['database'])

        # Курсор для выполнения операций с базой данных
        self.cursor = self.connection.cursor()
        # Распечатать сведения о PostgreSQL
        print("Информация о сервере PostgreSQL")
        print(self.connection.get_dsn_parameters(), "\n")
        # Выполнение SQL-запроса
        self.cursor.execute("SELECT version();")
        # Получить результат
        record = self.cursor.fetchone()
        print("Вы подключены к - ", record, "\n")

        commands = (
            """
            CREATE TABLE IF NOT EXISTS "tag"(
                "tag_id" INTEGER GENERATED ALWAYS AS IDENTITY,
                "text" text NOT NULL,
                PRIMARY KEY ("tag_id")
            );
            """,
            """                 
           CREATE TABLE IF NOT EXISTS "users"(
                "user_id" INTEGER GENERATED ALWAYS AS IDENTITY(0,1),
                "vk_id" INTEGER UNIQUE NOT NULL, 
                "quotes" INTEGER[],
                "tag" INTEGER[],
                "alias" VARCHAR(20) UNIQUE NOT NULL,
                "state" INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY ("user_id")
            );
            """,
            """                 
            CREATE TABLE IF NOT EXISTS "authors"(
                "author_id" INTEGER GENERATED ALWAYS AS IDENTITY,
                "title" VARCHAR UNIQUE NOT NULL,
                "quotes" INTEGER[] ,
                PRIMARY KEY ("author_id")
            );
            """,
            """            
            CREATE TABLE IF NOT EXISTS "quote"(
                "quote_id" INTEGER GENERATED ALWAYS AS IDENTITY,
                "user_id" INTEGER NOT NULL, 
                "author_id" INTEGER NOT NULL, 
                "text" TEXT NOT NULL,
                "tag" INTEGER[],
                "attachment" VARCHAR(32),
                "public" BOOL NOT NULL,
                PRIMARY KEY ("quote_id"),
                FOREIGN KEY ("user_id")  REFERENCES "users" ("user_id"),
                FOREIGN KEY ("author_id")  REFERENCES "authors" ("author_id")
            );
            """
        )

        for command in commands:
            self.cursor.execute(command)
            self.connection.commit()
            print("Таблица успешно создана в PostgreSQL")

    def close_connection(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Соединение с PostgreSQL закрыто")

    def user_exists(self, vk_id: int) -> bool:
        command = """
        SELECT EXISTS (SELECT "vk_id" FROM "users" WHERE "vk_id" = {vk_id});
        """.format(vk_id=vk_id)
        self.cursor.execute(command)
        user_exists = self.cursor.fetchone()
        return user_exists

    def alias_exists(self, alias: str) -> bool:
        command = """
        SELECT EXISTS (SELECT "alias" FROM "users" WHERE "alias" = {alias});
        """.format(alias=alias)
        self.cursor.execute(command)
        alias_exists = self.cursor.fetchone()
        return alias_exists

    def create_user(self, vk_id: int, alias: str):
        command = """
        INSERT INTO "users"("vk_id", "quotes","tag","alias"
        VALUES ({}, NULL, NULL, '{}');
        """.format(vk_id, alias)
        self.cursor.execute(command)
        self.connection.commit()

    def set_user_state(self, vk_id: int, state: State):
        command = """
        UPDATE "users"
        SET "state" = {state}
        WHERE "vk_id" = {vk_id};
        """.format(vk_id=vk_id, state=state.value)
        self.cursor.execute(command)
        self.connection.commit()

    def get_user_state(self, vk_id: int) -> State:
        command = """
        SELECT "state" FROM "users"
        WHERE "vk_id" = {vk_id};
        """.format(vk_id=vk_id)
        self.cursor.execute(command)
        state = self.cursor.fetchone()
        return State(state)

    def set_user_alias(self, vk_id: int, alias: str):
        command = """
                UPDATE "users"
                SET "alias" = '{alias}'
                WHERE "vk_id" = {vk_id};
                """.format(vk_id=vk_id, alias=alias)
        self.cursor.execute(command)
        self.connection.commit()

    def create_quote(self, vk_id: int, text: str, *, tags=None, author='', attachments=None, private=False) -> int:
        if tags is None:
            tags = []
        if attachments is None:
            attachments = []

        command = """
        DO $$
            DECLARE myid quote.quote_id%TYPE;
            DECLARE autid authors.author_id%TYPE;
        BEGIN
            INSERT INTO  "authors"  ("title") 
            VALUES ('{author}') ON CONFLICT("title") DO UPDATE SET title=EXCLUDED.title
            RETURNING "author_id" INTO autid;
           
            INSERT INTO "quote" ("user_id",	"author_id", "text","tag","attachment","public")
            VALUES ((SELECT "user_id" FROM "users" WHERE "vk_id" = {vk_id}), autid, '{text}', NULL, NULL, '1')
            RETURNING "quote_id" INTO myid;
            
            UPDATE "authors"
            SET "quotes" = array_append("quotes", myid)
            WHERE "author_id" = autid;
            
            UPDATE "users"
            SET "quotes" = array_append("quotes", myid)
            WHERE "vk_id" = {vk_id};
        END $$
        """
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
