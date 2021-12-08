# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from src.bot_base import BotBase

if __name__ == '__main__':
    with open('access_data.json') as json_file:
        data = json.load(json_file)

    group_id = data['group_id']
    token = data['token']

    bot = BotBase(group_id, token)
