# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from src.bot_base import BotBase

if __name__ == '__main__':
    with open('access_data.json') as json_file:
        data = json.load(json_file)

    group_auth = data['group_auth']
    database_auth = data['database_auth']

    bot = BotBase(group_auth=group_auth, database_auth=database_auth)
    bot.run()
