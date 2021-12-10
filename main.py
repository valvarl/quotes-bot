# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import traceback


from src.bot_base import BotBase, BotRuntimeError


def logs(s):
    with open('logs.txt', 'a+', encoding='utf8') as df:
        df.write(s + '\n')


if __name__ == '__main__':
    with open('access_data.json') as json_file:
        data = json.load(json_file)

    group_auth = data['group_auth']
    database_auth = data['database_auth']

    bot = BotBase(group_auth=group_auth, database_auth=database_auth)

    while True:
        try:
            bot.run()
        except BotRuntimeError as e:
            logs('Error accrued with code {}: {}\n'.format(e.code.value, e.what))
        except Exception as e:
            logs('Error:\n' + traceback.format_exc())
