# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
import requests
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


class BotRuntimeError(Exception):
    class ErrorCodes(Enum):
        TYPE_ERROR = 0

    def __init__(self, code: ErrorCodes, what: str, need_reply: bool, *, reply=''):
        self.code = code
        self.what = what
        self.need_reply = need_reply
        self.reply = reply


class State(Enum):
    ALIAS_INPUT = 0     # entering pseudonym
    BOT_MENU = 1        # bot main menu
    QUOTE_CREATION = 2  # creating quote
    QUOTE_SEARCH = 3    # searching quote
    MY_QUOTES = 4       # handling user's quotes
    ALIAS_CHANGING = 5  # changing of pseudonym


class Command(Enum):
    CREATE_QUOTE = 0


def check_args(args: dict):
    for variable_name, params in args.items():
        value, variable_type = params
        if type(value) != variable_type:
            what = "{} expected in {}".format(variable_type.__name__, variable_name)
            raise BotRuntimeError(BotRuntimeError.ErrorCodes.TYPE_ERROR.value, what, False)


class BotBase:
    class ParseResult:
        def __init__(self, bot_command: bool, *, text='', tags=None, author='', attachments=None):
            if tags is None:
                tags = []

            if attachments is None:
                attachments = []

            check_args({'bot_command': (bot_command, bool),
                        'text': (text, str),
                        'tags': (tags, list),
                        'author': (author, str),
                        'attachments': (attachments, list)})

            self.bot_command = bot_command
            self.text = text
            self.tags = tags
            self.author = author
            self.attachments = attachments

    def __init__(self, group_token: str, group_id: str):
        self.group_token = group_token
        self.group_id = group_id
        self.bot_session = vk_api.VkApi(token=self.group_token)
        self.bot_api = self.bot_session.get_api()

    def initialize_data(self):
        pass

    def run(self):
        while True:
            longpoll = VkBotLongPoll(self.bot_session, self.group_id)
            try:
                print('wait')
                for event in longpoll.listen():
                    print('got event')
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        self.manage_event(event)

            except requests.exceptions.ReadTimeout as timeout:
                continue

    def manage_event(self, event):
        print('message')
        if event.from_user:
            print(event.message['from_id'])
            self.send_message(peer_id=event.message['peer_id'], message=event.message['text'])

    def on_message(self):
        pass

    def parse_message(self, message) -> ParseResult:
        pass

    def get_keyboard(self, state: State):
        pass

    def send_message(self, peer_id: int, message: str):
        check_args({'peer_id': (peer_id, int), 'message': (message, str)})
        self.bot_api.messages.send(
            random_id=random.getrandbits(32),
            peer_id=peer_id,
            message=message
        )
