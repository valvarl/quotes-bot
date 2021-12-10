# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
import re
import requests
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from src.database import Database
from src.phrases import UserPhrases, GroupPhrases, ErrorPhrases
from src.keyboard import Keyboard, create_keyboard

VK_MESSAGE_LIMIT = 4096
QUOTE_LENGTH_LIMIT = 500
RANDOM_SEARCH_QUOTES_AMOUNT = 5


class BotRuntimeError(Exception):
    class ErrorCodes(Enum):
        TYPE_ERROR = 0
        KEYBOARD_ERROR = 1
        COMMAND_ERROR = 2
        PARSE_ERROR = 3

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
    QUOTE_ADDING = 6  # adding quote
    QUOTE_DELETING = 7  # deleting quote
    SEARCH_BY_TAG = 8  # searching by tag
    SEARCH_BY_WORD = 9  # searching by word


class Command(Enum):
    BOT_START = 0
    CREATE_QUOTE = 1
    SEARCH_QUOTE = 2
    MY_QUOTES = 3
    SEARCH_BY_WORD = 4
    SEARCH_BY_TAG = 5
    RANDOM_SEARCH = 6
    ADD_QUOTE = 7
    DELETE_QUOTE = 8
    CHANGE_ALIAS = 9
    FAQ = 10
    RETURN = 11
    NOT_FOUND = 12


def check_args(args: dict):
    for variable_name, params in args.items():
        value, variable_type = params
        if type(value) != variable_type:
            what = "{} expected in {}".format(variable_type.__name__, variable_name)
            raise BotRuntimeError(BotRuntimeError.ErrorCodes.TYPE_ERROR.value, what, False)


class BotBase:
    class ParseResult:
        def __init__(self, bot_command: bool, *, command: Command, text='', tags=None, author='', private=False):
            if tags is None:
                tags = []

            check_args({'bot_command': (bot_command, bool),
                        'command': (command, Command),
                        'text': (text, str),
                        'author': (author, str),
                        'tags': (tags, list),
                        'private': (private, bool)})

            self.bot_command = bot_command
            self.command = command
            self.text = text
            self.tags = tags
            self.author = author
            self.private = private

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
                    try:
                        self.on_message(event)
                    except BotRuntimeError as e:
                        if e.need_reply:
                            reply = "Ошибка: {}.".format(e.reply)
                            self.send_message(peer_id=event.message.from_id, message=reply)
                        else:
                            raise e

            except requests.exceptions.ReadTimeout:
                continue

    def create_user(self, vk_id: int):
        self.db.create_user(vk_id=vk_id)
        self.db.set_user_state(vk_id=vk_id, state=State.ALIAS_INPUT)
        self.send_message(peer_id=vk_id, message=GroupPhrases.ALIAS_INPUT.value)

    def get_quote(self, quote_id: int, print_quote_id=False) -> tuple:
        quote_data = self.db.get_quote(quote_id=quote_id)
        quote = quote_data['text'] + '\n©' + quote_data['author']
        if print_quote_id:
            quote = '<{}>\n'.format(quote_id) + quote
        return quote, quote_data['attachments']

    def print_quote_list(self, vk_id: int, quotes: list, keyboard: Keyboard, print_quote_id=False):
        message_rely = ''
        for quote in quotes:
            new_quote = self.get_quote(quote, print_quote_id)
            if not new_quote[1]:
                if len(message_rely) + len(new_quote[0]) + 2 < VK_MESSAGE_LIMIT:
                    message_rely += "\n\n" + new_quote[0]
                else:
                    self.send_message(peer_id=vk_id, message=message_rely, keyboard=keyboard)
                    message_rely = new_quote[0]
            else:
                if message_rely:
                    self.send_message(peer_id=vk_id, message=message_rely, keyboard=keyboard)
                    message_rely = ''
                self.send_message(peer_id=vk_id, message=new_quote[0], attachments=new_quote[1], keyboard=keyboard)
        if message_rely:
            self.send_message(peer_id=vk_id, message=message_rely, keyboard=keyboard)

    def on_message(self, event: vk_api.bot_longpoll.VkBotMessageEvent):
        if event.type == VkBotEventType.MESSAGE_NEW:
            parse_result = self.parse_message(event.message['text'])
            if parse_result.bot_command:
                if not self.db.user_exists(vk_id=event.message.from_id):
                    self.create_user(event.message.from_id)

                elif parse_result.command == Command.BOT_START:
                    print("BOT_START")
                    self.send_message(peer_id=event.message.from_id, keyboard=Keyboard.BOT_MENU)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.BOT_MENU)

                elif parse_result.command == Command.CREATE_QUOTE:
                    print("CREATE_QUOTE")
                    quote_id = self.db.create_quote(vk_id=event.message.from_id, text=parse_result.text,
                                                    tags=parse_result.tags, author=parse_result.author,
                                                    attachments=event.message.attachments,
                                                    private=parse_result.private)
                    quote = self.get_quote(quote_id=quote_id)
                    self.send_message(peer_id=event.message.from_id,
                                      message="Цитата добавлена:\n\n" + quote[0], attachments=quote[1],
                                      keyboard=Keyboard.BOT_MENU if self.db.get_user_state(
                                          event.message.from_id) == State.BOT_MENU else Keyboard.MY_QUOTES)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.QUOTE_CREATION)

                elif parse_result.command == Command.MY_QUOTES:
                    print("MY_QUOTES")
                    quotes = self.db.get_user_quotes(vk_id=event.message.from_id)
                    self.print_quote_list(vk_id=event.message.from_id, quotes=quotes, keyboard=Keyboard.MY_QUOTES)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.MY_QUOTES)

                elif parse_result.command == Command.SEARCH_QUOTE:
                    print("SEARCH_QUOTE")
                    self.send_message(peer_id=event.message.from_id, keyboard=Keyboard.QUOTE_SEARCH)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.QUOTE_SEARCH)

                elif parse_result.command == Command.ADD_QUOTE:
                    print("ADD_QUOTE")
                    self.send_message(peer_id=event.message.from_id, keyboard=Keyboard.QUOTE_SEARCH)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.QUOTE_SEARCH)

                elif parse_result.command == Command.DELETE_QUOTE:
                    print("DELETE_QUOTE")
                    self.send_message(peer_id=event.message.from_id, keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.QUOTE_DELETING)

                elif parse_result.command == Command.SEARCH_BY_TAG:
                    print("SEARCH_BY_TAG")
                    self.send_message(peer_id=event.message.from_id, keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.SEARCH_BY_TAG)

                elif parse_result.command == Command.SEARCH_BY_WORD:
                    print("SEARCH_BY_WORD")
                    self.send_message(peer_id=event.message.from_id, keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=event.message.from_id, state=State.SEARCH_BY_WORD)

                elif parse_result.command == Command.RANDOM_SEARCH:
                    print("RANDOM_SEARCH")
                    quotes = self.db.get_quotes_on_random(max_amount=RANDOM_SEARCH_QUOTES_AMOUNT)
                    self.print_quote_list(vk_id=event.message.from_id, quotes=quotes, keyboard=Keyboard.MY_QUOTES,
                                          print_quote_id=True)

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
        else:
            if message[0] == '@':
                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, 'empty quote', True,
                                      reply=ErrorPhrases.QUOTE_CREATION_ERROR_1.value)
            else:
                splited = re.split(r'@', raw_message)
                text = splited[0].strip()
                if len(text) > QUOTE_LENGTH_LIMIT:
                    raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "quote length limit exceeded",
                                          True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_11.value)
                author = ''
                private = False
                tags = []
                for param in splited[1:]:
                    if not param:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "empty param passed", True,
                                              reply=ErrorPhrases.QUOTE_CREATION_ERROR_2.value)
                    elif param[:2] not in ['a ', 't ', 'p ']:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "unknown param passed", True,
                                              reply=ErrorPhrases.QUOTE_CREATION_ERROR_3.value)
                    if param[0] == 'a':
                        if author is not '':
                            raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "several authors passed",
                                                  True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_6.value)
                        author_name = param[1:].strip()
                        if author_name[0] == '"' and author_name[-1] == '"':
                            if not len(author_name[1:-1]):
                                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "empty quotes passed",
                                                      True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_4.value)
                            elif author_name[1:-1].count('"'):
                                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "several authors passed",
                                                      True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_5.value)
                            author = author_name[1:-1]

                        else:
                            if author_name.count(' '):
                                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "quotes expected",
                                                      True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_7.value)
                            else:
                                author = author_name
                    elif param[0] == 't':
                        if tags is not None:
                            raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "several tag param passed",
                                                  True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_8.value)
                        tag_args = param[1:].strip()
                        if tag_args[0] == '"' and tag_args[-1] == '"':
                            if not len(tag_args[1:-1]):
                                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "empty quotes passed",
                                                      True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_4.value)
                            elif tag_args[1:-1].count('"'):
                                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR,
                                                      "several quotes args passed",
                                                      True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_9.value)
                            tags = tag_args[1:-1].split()
                        else:
                            if tag_args.count(' '):
                                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "quotes expected",
                                                      True, reply=ErrorPhrases.QUOTE_CREATION_ERROR_10.value)
                            else:
                                tags = [tag_args]
                    else:
                        private = True

                return self.ParseResult(False, command=Command.NOT_FOUND,
                                        text=text, tags=tags, author=author, private=private)

    def get_keyboard(self, state: State):
        pass

    def send_message(self, peer_id: int, *, message='', attachments=None, keyboard=Keyboard.EMPTY):
        if attachments is None:
            attachments = []
        check_args({'peer_id': (peer_id, int), 'message': (message, str), 'attachments': (attachments, list),
                    'keyboard': (keyboard, Keyboard)})
        self.bot_api.messages.send(
            random_id=random.getrandbits(32),
            peer_id=peer_id,
            message=message,
            attachments=attachments,
            keyboard=None if keyboard == Keyboard.EMPTY else create_keyboard(keyboard)
        )
