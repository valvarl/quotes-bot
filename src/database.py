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
            CREATE TABLE IF NOT EXISTS tags (
                tag_id INTEGER GENERATED ALWAYS AS IDENTITY,
                "text" VARCHAR(20) UNIQUE NOT NULL,
                quotes INTEGER[],
                PRIMARY KEY (tag_id)
            );
            """,
            """                 
            CREATE TABLE IF NOT EXISTS "users"(
                "user_id" INTEGER GENERATED ALWAYS AS IDENTITY,
                "vk_id" INTEGER UNIQUE NOT NULL, 
                "quotes" INTEGER[],
                "tags" INTEGER[],
                "alias" VARCHAR(20) UNIQUE NOT NULL,
                "state" INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY ("user_id")
            );
            """,
            """                 
            CREATE TABLE IF NOT EXISTS "authors"(
                "author_id" INTEGER GENERATED ALWAYS AS IDENTITY,
                "title" VARCHAR(20) UNIQUE NOT NULL,
                "quotes" INTEGER[] ,
                PRIMARY KEY ("author_id")
            );
            """,
            """            
            CREATE TABLE IF NOT EXISTS "quotes"(
                "quote_id" INTEGER GENERATED ALWAYS AS IDENTITY,
                "user_id" INTEGER NOT NULL, 
                "author_id" INTEGER NOT NULL, 
                "text" VARCHAR(500) NOT NULL,
                "tags" INTEGER[],
                "attachment" VARCHAR(32),
                "private" BOOL NOT NULL,
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
        user_exists = self.cursor.fetchone()[0]
        return user_exists

    def alias_exists(self, alias: str) -> bool:
        command = """
        SELECT EXISTS (SELECT "alias" FROM "users" WHERE "alias" = '{alias}');
        """.format(alias=alias)
        self.cursor.execute(command)
        alias_exists = self.cursor.fetchone()[0]
        return alias_exists

    def create_user(self, vk_id: int, alias: str):
        command = """
        INSERT INTO "users" ("vk_id", "quotes", "tags", "alias")
        VALUES ({vk_id}, NULL, NULL, '{alias}');
        """.format(vk_id=vk_id, alias=alias)
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
        state = self.cursor.fetchone()[0]
        print(state)
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

        tags_str = ', '.join(["('{}')".format(x) for x in tags])

        command = """
        DO $$
            DECLARE q_id quotes.quote_id%TYPE;
            DECLARE a_id authors.author_id%TYPE;
            DECLARE tags_arr INTEGER[];
        BEGIN
            WITH ins AS (
                INSERT INTO tags ("text") VALUES {tags}
                ON CONFLICT("text") DO UPDATE SET "text"=EXCLUDED."text" RETURNING tag_id)
            SELECT array_agg(tag_id) INTO tags_arr FROM ins;
        
            INSERT INTO authors ("title") 
            VALUES ('{author}') ON CONFLICT(title) DO UPDATE SET title=EXCLUDED.title
            RETURNING author_id INTO a_id;
        
            INSERT INTO quotes (user_id, author_id, "text", tags, attachment, "private")
            VALUES ((SELECT user_id FROM users WHERE vk_id = {vk_id}), a_id, '{text}', tags_arr, '{attachment}', '{private}')
            RETURNING quote_id INTO q_id;
        
            UPDATE authors
            SET quotes = array_append(quotes, q_id)
            WHERE author_id = a_id;
        
            UPDATE users
            SET 
                quotes = array_append(quotes, q_id),
                tags = (SELECT array_agg(arr ORDER BY arr) from (SELECT DISTINCT unnest(tags || tags_arr) AS arr) s)
            WHERE vk_id = {vk_id};
            
            UPDATE tags 
            SET quotes = array_append(quotes, q_id) 
            WHERE tags.tag_id = ANY (tags_arr::int[]);
            SELECT "quote_id" FROM "quotes" WHERE "quote_id" = q_id;
        END $$
        SELECT MAX("quote_id") FROM "quotes"
        INNER JOIN "users"
        ON "quotes"."user_id" = "users"."user_id"
        WHERE "text" = '{text}' and "vk_id" = {vk_id};
        """.format(vk_id=vk_id, text=text, tags=tags_str, author=author, private=(1 if private else 0),
                   attachment=(attachments[0] if len(attachments) > 0 else 'NULL'))
        quote_id = self.cursor.fetchone()[0]
        print(quote_id)
        self.connection.commit()
        return quote_id

    def get_quote(self, quote_id: int) -> dict:
        command = f"""
        SELECT "vk_id", "title", "text", "attachment", "private" FROM "quotes"
        INNER JOIN "authors"
        ON "quotes"."author_id" = "authors"."author_id"
        INNER JOIN "users"
        ON "quotes"."user_id" = "users"."user_id"
        WHERE "quote_id"={quote_id};
        """
        quote_id = self.cursor.execute(command)
        print(quote_id)

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
        command = f"""
        SELECT "quote_id" FROM "quotes"
        INNER JOIN "users"
        ON "quotes"."user_id" = "users"."user_id"
        WHERE "vk_id" = {vk_id};
        """
        quote_ids = self.cursor.fetchall()
        print()
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

import json
if __name__ == '__main__':
    with open('../access_data.json') as json_file:
        data = json.load(json_file)

    group_auth = data['group_auth']
    database_auth = data['database_auth']
    db = Database(database_auth)
    print(db.get_quote(3))