# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.methods import State, SearchParams


class Database:
    def __init__(self, database_auth: dict):
        try:
            self.connection, self.cursor = None, None
            self.create_database(database_auth=database_auth)
            self.create_tables(database_auth=database_auth)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
            self.close_connection()

    def create_database(self, database_auth: dict):
        self.connection = psycopg2.connect(user=database_auth['user'],
                                           password=database_auth['password'],
                                           host=database_auth['host'],
                                           port=database_auth['port'])
        self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.connection.cursor()
        self.cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{database_auth['database']}'")
        exists = self.cursor.fetchone()
        if not exists:
            self.cursor.execute(f"CREATE DATABASE {database_auth['database']}")
            self.close_connection()

    def create_tables(self, database_auth: dict):
        self.connection = psycopg2.connect(user=database_auth['user'],
                                           password=database_auth['password'],
                                           host=database_auth['host'],
                                           port=database_auth['port'],
                                           database=database_auth['database'])

        self.cursor = self.connection.cursor()
        print("Информация о сервере PostgreSQL")
        print(self.connection.get_dsn_parameters(), "\n")
        self.cursor.execute("SELECT version();")
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
                "attachment" VARCHAR(64),
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
        command = f"""SELECT EXISTS (SELECT "vk_id" FROM "users" WHERE "vk_id" = {vk_id});"""
        self.cursor.execute(command)
        user_exists = self.cursor.fetchone()[0]
        return user_exists

    def alias_exists(self, alias: str) -> bool:
        command = f"""SELECT EXISTS (SELECT "alias" FROM "users" WHERE "alias" = '{alias}');"""
        self.cursor.execute(command)
        alias_exists = self.cursor.fetchone()[0]
        return alias_exists

    def create_user(self, vk_id: int, alias: str):
        command = f"""
        INSERT INTO "users" ("vk_id", "quotes", "tags", "alias")
        VALUES ({vk_id}, NULL, NULL, '{alias}');
        """
        self.cursor.execute(command)
        self.connection.commit()

    def set_user_state(self, vk_id: int, state: State):
        command = f"""UPDATE "users" SET "state" = {state.value} WHERE "vk_id" = {vk_id};"""
        self.cursor.execute(command)
        self.connection.commit()

    def get_user_state(self, vk_id: int) -> State:
        command = f"""SELECT "state" FROM "users" WHERE "vk_id" = {vk_id};"""
        self.cursor.execute(command)
        state = self.cursor.fetchone()[0]
        print(state)
        return State(state)

    def get_user_alias(self, vk_id: int) -> str:
        command = f"""SELECT "alias" FROM "users" WHERE "vk_id" = {vk_id};"""
        self.cursor.execute(command)
        alias = self.cursor.fetchone()[0]
        print(alias)
        return alias

    def set_user_alias(self, vk_id: int, alias: str):
        command = f"""UPDATE "users" SET "alias" = '{alias}' WHERE "vk_id" = {vk_id};"""
        self.cursor.execute(command)
        self.connection.commit()

    def create_quote(self, vk_id: int, text: str, *, tags=None, author='', attachments=None, private=False) -> int:
        if tags is None:
            tags = []
        if attachments is None:
            attachments = []

        tags_str = ', '.join(["('{}')".format(x) for x in list(set(tags))])

        create_tags_arr = f"""
        WITH ins AS (
        INSERT INTO tags ("text") VALUES {tags_str}
        ON CONFLICT("text") DO UPDATE SET "text"=EXCLUDED."text" RETURNING tag_id)
        SELECT array_agg(tag_id) INTO tags_arr FROM ins;
        """ if tags else ''

        create_attachment = f"attachment = '{attachments[0]}';" if attachments else ''

        command = """
        DO $$
            DECLARE q_id quotes.quote_id%TYPE;
            DECLARE attachment quotes.attachment%TYPE;
            DECLARE a_id authors.author_id%TYPE;
            DECLARE tags_arr INTEGER[];
        BEGIN
            {create_tags_arr}
            {create_attachment}

            INSERT INTO authors ("title") 
            VALUES ('{author}') ON CONFLICT(title) DO UPDATE SET title=EXCLUDED.title
            RETURNING author_id INTO a_id;

            INSERT INTO quotes (user_id, author_id, "text", tags, attachment, "private")
            VALUES (
                (SELECT user_id FROM users WHERE vk_id = {vk_id}), a_id, '{text}', tags_arr, attachment, '{private}'
            )
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
        END $$;
        SELECT MAX("quote_id") FROM "quotes"
        INNER JOIN "users"
        ON "quotes"."user_id" = "users"."user_id"
        WHERE "text" = '{text}' and "vk_id" = {vk_id};
        """.format(vk_id=vk_id, text=text, tags=tags_str, author=author, private=(1 if private else 0),
                   create_tags_arr=create_tags_arr, create_attachment=create_attachment)
        print(command)
        self.cursor.execute(command)
        quote_id = self.cursor.fetchone()[0]
        self.connection.commit()
        print(quote_id)
        return quote_id

    def add_quote_to_user(self, vk_id: int, quote_id: int):
        command = """
        UPDATE users
        SET quotes[1]={quote_id}
        WHERE  vk_id = {vk_id} and ((select quotes is null from users WHERE vk_id = {vk_id}) = 'true');
        UPDATE users
        SET quotes = array_append(quotes, {quote_id})
        WHERE  vk_id = {vk_id} and not ("quotes" @> '{{ {quote_id} }}'::integer[]);
        """.format(quote_id=quote_id, vk_id=vk_id)
        self.cursor.execute(command)
        self.connection.commit()

    def remove_user_quote(self, vk_id: int, quote_id: int):
        command = f"""
        UPDATE users
        SET quotes = array_remove( quotes, {quote_id} )  
        WHERE vk_id= {vk_id} and (quotes @> '{{{quote_id}}}'::INT[]);
        update quotes
        set private = '1'
        where private = '0' and quote_id={quote_id} and not exists((select quotes from users
        where (quotes @> '{{{quote_id}}}'::INT[]) group by quotes having count(quotes)=1));
        """
        self.cursor.execute(command)
        self.connection.commit()

    def get_quote(self, quote_id: int) -> dict or None:
        command = f"""
        SELECT "vk_id", "title", "text", "attachment", "private" FROM "quotes"
        INNER JOIN "authors"
        ON "quotes"."author_id" = "authors"."author_id"
        INNER JOIN "users"
        ON "quotes"."user_id" = "users"."user_id"
        WHERE "quote_id"={quote_id};
        """
        self.cursor.execute(command)
        quote = self.cursor.fetchone()

        print(quote)
        if quote is None:
            return quote

        request_result = {
            'vk_id': quote[0],  # vk_id of creator
            'author': quote[1],
            'text': quote[2],
            'attachments': [quote[3]] if quote[3] is not None else [],
            'private': quote[4]
        }
        print(request_result)
        return request_result

    def get_user_quotes(self, vk_id: int) -> list:
        command = f"""
        SELECT "quote_id" FROM "quotes"
        INNER JOIN "users"
        ON "quotes"."user_id" = "users"."user_id"
        WHERE "vk_id" = {vk_id};
        """
        self.cursor.execute(command)
        quote_ids = [x[0] for x in self.cursor.fetchall()]
        return quote_ids

    def get_my_quotes(self, vk_id: int) -> list:
        command = f"""
        SELECT "quotes" FROM "users" 
        WHERE "vk_id" = {vk_id};
        """
        self.cursor.execute(command)
        quote_ids = self.cursor.fetchone()[0]
        print(quote_ids)
        return quote_ids

    def get_quotes_on_random(self, max_amount: int) -> list:
        command = f"""
        SELECT "quote_id" FROM "quotes"
        WHERE "private" = '0'
        ORDER BY RANDOM()
        LIMIT {max_amount};
        """
        self.cursor.execute(command)
        quote_ids = [x[0] for x in self.cursor.fetchall()]
        return quote_ids

    def get_quotes_by_word(self, vk_id: int, word_states: list, search_param: SearchParams, max_amount: int) -> list:
        word_states = ', '.join(["'%{}%'".format(x) for x in word_states])
        print(word_states)
        commands = (f"""
        ---ищет среди всех и своих и чужих публичных
        SELECT "quote_id" FROM "quotes" WHERE ("quote_id" = ANY((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[]) OR(
        "quote_id" <> ALL((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[]) AND "private" = '0'
        )) AND "text" ILIKE ANY(ARRAY[{word_states}])
        ORDER BY RANDOM()
        LIMIT {max_amount};
        """, f"""
        --- ищет по всем своим, которые написаны vk_id и добавлены 
        SELECT "quote_id" FROM "quotes" 
        WHERE "quote_id" = ANY((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[]) AND "text" ILIKE ANY(ARRAY[{word_states}])
        ORDER BY RANDOM()
        LIMIT {max_amount};					
        """, f"""
        ---поиск по высказываниям других пользователей
        SELECT "quote_id" FROM "quotes" WHERE "quote_id" <> ALL((
        SELECT "quotes" FROM "users" WHERE "vk_id" ={vk_id})::int[]) 
        AND "private" = '0' AND "text" ILIKE ANY(ARRAY[{word_states}])
        ORDER BY RANDOM()
        LIMIT {max_amount};
        """)
        print(commands)
        self.cursor.execute(commands[search_param.value])
        quote_ids = [x[0] for x in self.cursor.fetchall()]
        return quote_ids

    def get_quotes_by_tag(self, vk_id: int, tags: list, search_param: SearchParams, max_amount: int) -> list:
        tags_arr = ', '.join(["'{}'".format(x) for x in tags])
        commands = (f"""
        ---ищет среди всех и своих и чужих публичных
        SELECT "quote_id" FROM "quotes" WHERE ("quote_id" = ANY((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[]) OR(
        "quote_id" <> ALL((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[]) AND "private" = '0'
        )) AND "tags" && (SELECT ARRAY_AGG("tag_id") FROM "tags" WHERE "text" ILIKE ANY(ARRAY[{tags_arr}]))
        ORDER BY RANDOM()
        LIMIT {max_amount};
        """, f"""
        --- ищет по всем своим, которые написаны vk_id и добавлены 
        SELECT "quote_id" FROM "quotes" WHERE "quote_id" = ANY((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[])
        AND "tags" && (SELECT ARRAY_AGG("tag_id") FROM "tags" WHERE "text" ILIKE ANY(ARRAY[{tags_arr}]))
        ORDER BY RANDOM()
        LIMIT {max_amount};					
        """, f"""
        ---поиск по высказываниям других пользователей
        SELECT "quote_id" FROM "quotes" WHERE "quote_id" <> ALL((SELECT "quotes" FROM "users" WHERE "vk_id" = {vk_id})::int[]) AND "private" = '0'
        AND "tags" && (SELECT ARRAY_AGG("tag_id") FROM "tags" WHERE "text" ILIKE ANY(ARRAY[{tags_arr}]))   
        ORDER BY RANDOM()
        LIMIT {max_amount};
        """)
        print(commands)
        self.cursor.execute(commands[search_param.value])
        quote_ids = [x[0] for x in self.cursor.fetchall()]
        return quote_ids
