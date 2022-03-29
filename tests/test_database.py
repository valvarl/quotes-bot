import unittest

from src.database import Database
from src.methods import State
import json
from random import randint
import random, string


def generate_random_string(length):
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string


class MyTestCase(unittest.TestCase):
    def setUp(self):
        with open('../access_data.json') as json_file:
            data = json.load(json_file)
            database_auth = data['database_auth']

        self.db = Database(database_auth)

    def test_close_connection(self):
        self.db.close_connection()

    def test_create_user(self):
        vk_id = randint(0, 1000000)
        alias = generate_random_string(10)
        self.db.create_user(vk_id, alias)
        self.assertTrue(self.db.user_exists(vk_id))

    def test_alias_exists(self):
        vk_id = randint(0, 1000000)
        alias = generate_random_string(10)
        self.db.create_user(vk_id, alias)
        self.assertTrue(self.db.alias_exists(alias))

    def test_user_state(self):
        vk_id = randint(0, 1000000)
        alias = generate_random_string(10)
        self.db.create_user(vk_id, alias)
        self.db.set_user_state(vk_id, State.BOT_MENU)
        self.assertEqual(self.db.get_user_state(vk_id), State.BOT_MENU)

    def test_create_quote(self):
        vk_id = randint(0, 1000000)
        alias = generate_random_string(10)
        quote = generate_random_string(10)
        self.db.create_user(vk_id, alias)
        quote_id = self.db.create_quote(vk_id, quote)
        self.assertIn(quote_id, self.db.get_my_quotes(vk_id))
        self.assertEqual(self.db.get_quote(quote_id)['text'], quote)


if __name__ == '__main__':
    unittest.main()
