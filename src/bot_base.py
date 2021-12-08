# ! /usr/bin/env python
# -*- coding: utf-8 -*-


from enum import Enum
import requests
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from methods import check_args


class BotRuntimeError(Exception):
    class ErrorCodes(Enum):
        TYPE_ERROR = 0

    def __init__(self, code: ErrorCodes, what: str, need_reply: bool, *, reply=''):
        self.code = code
        self.what = what
        self.need_reply = need_reply
        self.reply = reply


class BotBase:
    class State(Enum):
        ALIAS_INPUT = 0     # entering pseudonym
        BOT_MENU = 1        # bot main menu
        QUOTE_CREATION = 2  # creating quote
        QUOTE_SEARCH = 3    # searching quote
        MY_QUOTES = 4       # handling user's quotes
        ALIAS_CHANGING = 5  # changing of pseudonym

    class Command(Enum):
        CREATE_QUOTE = 0

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

    def __init__(self, group_id: str, token: str):
        self.group_id = group_id
        self.token = token

    def initialize_data(self):
        pass

    def run(self):
        pass

    def on_message(self):
        pass

    def parse_message(self, message) -> ParseResult:
        pass

    def get_keyboard(self, state: State):
        pass

    def send_message(self):
        pass
