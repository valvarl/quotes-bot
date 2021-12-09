# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
import requests
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from src.database import Database
from src.phrases import UserPhrases, GroupPhrases


class BotRuntimeError(Exception):
    class ErrorCodes(Enum):
        TYPE_ERROR = 0
        KEYBOARD_ERROR = 1
        UNKNOWN_COMMAND = 2

    def __init__(self, code: ErrorCodes, what: str, need_reply: bool, *, reply=''):
        self.code = code
        self.what = what
        self.need_reply = need_reply
        self.reply = reply


class State(Enum):
    ALIAS_INPUT = 0  # entering pseudonym
    BOT_MENU = 1  # bot main menu
    QUOTE_CREATION = 2  # creating quote
    QUOTE_SEARCH = 3  # searching quote
    MY_QUOTES = 4  # handling user's quotes
    ALIAS_CHANGING = 5  # changing of pseudonym


class Command(Enum):
    BOT_START = 0
    CREATE_QUOTE = 1
    SEARCH_QUOTE = 2
    MY_QUOTES = 3
    SEARCH_BY_WORD = 4
    SEARCH_BY_TAG = 5
    ADD_QUOTE = 6
    DELETE_QUOTE = 7
    CHANGE_ALIAS = 8
    FAQ = 9
    RETURN = 10


def check_args(args: dict):
    for variable_name, params in args.items():
        value, variable_type = params
        if type(value) != variable_type:
            what = "{} expected in {}".format(variable_type.__name__, variable_name)
            raise BotRuntimeError(BotRuntimeError.ErrorCodes.TYPE_ERROR.value, what, False)


class BotBase:
    class ParseResult:
        def __init__(self, bot_command: bool, *, command: Command, text='', tags=None, author='', attachments=None):
            if tags is None:
                tags = []

            if attachments is None:
                attachments = []

            check_args({'bot_command': (bot_command, bool),
                        'command': (command, Command),
                        'text': (text, str),
                        'tags': (tags, list),
                        'author': (author, str),
                        'attachments': (attachments, list)})

            self.bot_command = bot_command
            self.command = command
            self.text = text
            self.tags = tags
            self.author = author
            self.attachments = attachments

    def __init__(self, group_auth: dict, database_auth: dict):
        check_args({'group_auth': (group_auth, dict),
                    'database_auth': (database_auth, dict)})
        self.group_token = group_auth['group_token']
        self.group_id = group_auth['group_id']
        self.bot_session = vk_api.VkApi(token=self.group_token)
        self.bot_api = self.bot_session.get_api()
        self.db = Database(database_auth)

    def initialize_data(self):
        pass

    def run(self):
        while True:
            longpoll = VkBotLongPoll(self.bot_session, self.group_id)
            try:
                print('wait')
                for event in longpoll.listen():
                    print('got event')
                    self.on_message(event)

            except requests.exceptions.ReadTimeout:
                continue

    def on_message(self, event: vk_api.bot_longpoll.VkBotMessageEvent):
        if event.type == VkBotEventType.MESSAGE_NEW:
            parse_result = self.parse_message(event.message['text'])
            if parse_result.bot_command:
                if parse_result.command == Command.BOT_START:
                    if self.db.user_exists(vk_id=event.message.from_id):
                        print("BOT_START, user exists")
                        self.db.set_user_state(vk_id=event.message.from_id, state=State.BOT_MENU)
                        self.send_message(peer_id=event.object.from_id, message=GroupPhrases.ALIAS_INPUT.value)
                    else:
                        print("BOT_START, user not exists")
                        self.db.create_user(vk_id=event.message.from_id)
                        self.db.set_user_state(vk_id=event.message.from_id, state=State.ALIAS_INPUT)
                        self.send_message(peer_id=event.object.from_id, message=GroupPhrases.ALIAS_INPUT.value)
                elif parse_result.command == Command.CREATE_QUOTE:
                    pass
                elif parse_result.command == Command.MY_QUOTES:
                    pass
                elif parse_result.command == Command.SEARCH_QUOTE:
                    pass
                elif parse_result.command == Command.ADD_QUOTE:
                    pass
                elif parse_result.command == Command.DELETE_QUOTE:
                    pass
                elif parse_result.command == Command.SEARCH_BY_TAG:
                    pass
                elif parse_result.command == Command.SEARCH_BY_WORD:
                    pass
                else:
                    raise BotRuntimeError(BotRuntimeError.ErrorCodes.UNKNOWN_COMMAND,
                                          "unknown command \"{}\"".format(parse_result.command), False)

            else:
                if self.db.user_exists(vk_id=event.message.from_id):
                    if self.db.get_user_state(vk_id=event.message.from_id) == State.ALIAS_INPUT:
                        self.db.set_user_alias(vk_id=event.message.from_id, alias=parse_result.text)
                        print("ALIAS_INPUT")
                else:
                    self.db.create_user(vk_id=event.message.from_id)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.ALIAS_INPUT)
                    self.send_message(peer_id=event.object.from_id, message=GroupPhrases.ALIAS_INPUT.value)

            print(event.message['from_id'], event.message['text'])
        elif event.type == VkBotEventType.MESSAGE_REPLY:
            if event.object.text == GroupPhrases.GREETINGS.value:
                self.db.create_user(vk_id=event.object.from_id)
                self.db.set_user_state(vk_id=event.object.from_id, state=State.ALIAS_INPUT)
                self.send_message(peer_id=event.object.from_id, message=GroupPhrases.ALIAS_INPUT.value)

    def parse_message(self, raw_message: str) -> ParseResult:
        message = raw_message.lower()
        if message in [UserPhrases.START_RUS, UserPhrases.START_EN]:
            return self.ParseResult(True, command=Command.BOT_START)
        elif message == UserPhrases.CREATE_QUOTE:
            return self.ParseResult(True, command=Command.CREATE_QUOTE)
        elif message == UserPhrases.ADD_QUOTE:
            return self.ParseResult(True, command=Command.ADD_QUOTE)
        elif message == UserPhrases.DELETE_QUOTE:
            return self.ParseResult(True, command=Command.DELETE_QUOTE)
        elif message == UserPhrases.SEARCH_BY_WORD:
            return self.ParseResult(True, command=Command.SEARCH_BY_WORD)
        elif message == UserPhrases.SEARCH_BY_WORD:
            return self.ParseResult(True, command=Command.SEARCH_BY_TAG)
        elif message == UserPhrases.MY_QUOTES:
            return self.ParseResult(True, command=Command.MY_QUOTES)
        elif message == UserPhrases.CHANGE_ALIAS:
            return self.ParseResult(True, command=Command.CHANGE_ALIAS)
        elif message == UserPhrases.FAQ:
            return self.ParseResult(True, command=Command.FAQ)
        elif message == UserPhrases.RETURN:
            return self.ParseResult(True, command=Command.RETURN)

    def get_keyboard(self, state: State):
        pass

    def send_message(self, peer_id: int, *, message: str, attachments=None):
        if attachments is None:
            attachments = []
        check_args({'peer_id': (peer_id, int), 'message': (message, str), 'attachments': (attachments, list)})
        self.bot_api.messages.send(
            random_id=random.getrandbits(32),
            peer_id=peer_id,
            message=message,
            attachments=attachments
        )
