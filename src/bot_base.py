# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
import re
import requests
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from src.database import Database, SearchParams, State
from src.phrases import UserPhrases, GroupPhrases, ErrorPhrases, KeyboardHints
from src.keyboard import Keyboard, create_keyboard
from src.methods import BotRuntimeError, get_word_states, check_args

VK_MESSAGE_LIMIT = 4096
QUOTE_LENGTH_LIMIT = 500
RANDOM_SEARCH_QUOTES_AMOUNT = 5
SEARCH_QUOTES_AMOUNT = 10


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


class BotBase:
    class ParseResult:
        def __init__(self, bot_command: bool, *, command=Command.NOT_FOUND, text='', tags=None, author='',
                     private=False, search_param=SearchParams.ALL):
            if tags is None:
                tags = []

            check_args({'bot_command': (bot_command, bool),
                        'command': (command, Command),
                        'text': (text, str),
                        'author': (author, str),
                        'tags': (tags, list),
                        'private': (private, bool),
                        'search_param': (search_param, SearchParams)})

            self.bot_command = bot_command
            self.command = command
            self.text = text
            self.tags = tags
            self.author = author
            self.private = private
            self.search_param = search_param

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
                            self.send_message(peer_id=event.message.from_id, message=reply, keyboard=e.keyboard)
                        else:
                            print(e.code.value, e.what)
                            raise e

            except requests.exceptions.ReadTimeout:
                continue

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
            vk_id = event.message.from_id
            user_exists = self.db.user_exists(vk_id=vk_id)
            user_state = self.db.get_user_state(vk_id=vk_id) if user_exists else State.ALIAS_INPUT
            try:
                parse_result = self.parse_message(raw_message=event.message['text'], state=user_state)
            except BotRuntimeError as e:
                if e.need_reply:
                    if user_state in [State.QUOTE_CREATION_BM, State.QUOTE_CREATION_MQ,
                                      State.SEARCH_BY_WORD, State.SEARCH_BY_WORD]:
                        e.keyboard = Keyboard.FAQ_AND_RETURN
                    elif user_state == State.ALIAS_CHANGING:
                        e.keyboard = Keyboard.RETURN
                raise e
            if parse_result.bot_command and user_exists or parse_result.command == Command.BOT_START:
                if parse_result.command == Command.BOT_START:
                    print("BOT_START")
                    if user_exists:
                        self.send_message(peer_id=vk_id, keyboard=Keyboard.BOT_MENU)
                        self.db.set_user_state(vk_id=vk_id, state=State.BOT_MENU)
                    else:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.ALIAS_INPUT.value)

                elif parse_result.command == Command.CREATE_QUOTE:
                    print("CREATE_QUOTE")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.QUOTE_CREATING.value,
                                      keyboard=Keyboard.FAQ_AND_RETURN)
                    if user_state == State.BOT_MENU:
                        self.db.set_user_state(vk_id=vk_id, state=State.QUOTE_CREATION_BM)
                    elif user_state == State.MY_QUOTES:
                        self.db.set_user_state(vk_id=vk_id, state=State.QUOTE_CREATION_MQ)
                    else:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.UNKNOWN_COMMAND,
                                              "unknown command \"{}\"".format(parse_result.command), False)

                elif parse_result.command == Command.MY_QUOTES:
                    print("MY_QUOTES")
                    quotes = self.db.get_user_quotes(vk_id=vk_id)
                    if quotes:
                        self.print_quote_list(vk_id=vk_id, quotes=quotes, keyboard=Keyboard.MY_QUOTES)
                    else:
                        self.send_message(peer_id=vk_id, message=KeyboardHints.MY_QUOTES_EMPTY.value,
                                          keyboard=Keyboard.MY_QUOTES)
                    self.db.set_user_state(vk_id=vk_id, state=State.MY_QUOTES)

                elif parse_result.command == Command.SEARCH_QUOTE:
                    print("SEARCH_QUOTE")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.SEARCH_MENU.value,
                                      keyboard=Keyboard.QUOTE_SEARCH)
                    self.db.set_user_state(vk_id=vk_id, state=State.QUOTE_SEARCH)

                elif parse_result.command == Command.ADD_QUOTE:
                    print("ADD_QUOTE")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.QUOTE_ADDING.value
                                      , keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=vk_id, state=State.QUOTE_ADDING)

                elif parse_result.command == Command.DELETE_QUOTE:
                    print("DELETE_QUOTE")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.QUOTE_DELETING.value,
                                      keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=vk_id, state=State.QUOTE_DELETING)

                elif parse_result.command == Command.SEARCH_BY_TAG:
                    print("SEARCH_BY_TAG")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.SEARCH_BY_TAG.value,
                                      keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=vk_id, state=State.SEARCH_BY_TAG)

                elif parse_result.command == Command.SEARCH_BY_WORD:
                    print("SEARCH_BY_WORD")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.SEARCH_BY_WORD.value,
                                      keyboard=Keyboard.FAQ_AND_RETURN)
                    self.db.set_user_state(vk_id=vk_id, state=State.SEARCH_BY_WORD)

                elif parse_result.command == Command.RANDOM_SEARCH:
                    print("RANDOM_SEARCH")
                    quotes = self.db.get_quotes_on_random(max_amount=RANDOM_SEARCH_QUOTES_AMOUNT)
                    self.print_quote_list(vk_id=vk_id, quotes=quotes, keyboard=Keyboard.QUOTE_SEARCH,
                                          print_quote_id=True)

                elif parse_result.command == Command.CHANGE_ALIAS:
                    print("CHANGE_ALIAS")
                    self.send_message(peer_id=vk_id, message=KeyboardHints.ALIAS_CHANGING.value,
                                      keyboard=Keyboard.RETURN)
                    self.db.set_user_state(vk_id=vk_id, state=State.ALIAS_CHANGING)

                elif parse_result.command == Command.RETURN:
                    if user_state in [State.SEARCH_BY_WORD, State.SEARCH_BY_TAG]:
                        self.db.set_user_state(vk_id=vk_id, state=State.QUOTE_SEARCH)
                        self.send_message(peer_id=vk_id, message=KeyboardHints.SEARCH_QUOTES_RETURN.value,
                                          keyboard=Keyboard.QUOTE_SEARCH)
                    elif user_state in [State.ALIAS_CHANGING, State.QUOTE_CREATION_BM, State.MY_QUOTES,
                                        State.QUOTE_SEARCH]:
                        self.db.set_user_state(vk_id=vk_id, state=State.BOT_MENU)
                        self.send_message(peer_id=vk_id, message=KeyboardHints.BOT_MENU_RETURN.value,
                                          keyboard=Keyboard.BOT_MENU)
                    elif user_state in [State.QUOTE_CREATION_MQ, State.QUOTE_ADDING, State.QUOTE_DELETING]:
                        self.db.set_user_state(vk_id=vk_id, state=State.MY_QUOTES)
                        self.send_message(peer_id=vk_id, message=KeyboardHints.MY_QUOTES_RETURN.value,
                                          keyboard=Keyboard.MY_QUOTES)
                    else:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.UNKNOWN_COMMAND,
                                              "unknown command \"{}\"".format(parse_result.command), False)

                elif parse_result.command == Command.FAQ:
                    if user_state in [State.QUOTE_CREATION_BM, State.QUOTE_CREATION_MQ]:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.QUOTE_FAQ.value,
                                          keyboard=Keyboard.RETURN)
                    elif user_state == State.QUOTE_DELETING:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.DELETE_FAQ.value,
                                          keyboard=Keyboard.RETURN)
                    elif user_state == State.QUOTE_ADDING:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.ADD_FAQ.value,
                                          keyboard=Keyboard.RETURN)
                    elif user_state == State.SEARCH_BY_WORD:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.SEARCH_BY_WORD_FAQ.value,
                                          keyboard=Keyboard.RETURN)
                    elif user_state == State.SEARCH_BY_TAG:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.SEARCH_BY_TAG_FAQ.value,
                                          keyboard=Keyboard.RETURN)
                    else:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.UNKNOWN_COMMAND,
                                              "unknown command \"{}\"".format(parse_result.command), False)

                else:
                    raise BotRuntimeError(BotRuntimeError.ErrorCodes.UNKNOWN_COMMAND,
                                          "unknown command \"{}\"".format(parse_result.command), False)

            else:
                if not user_exists:
                    if user_state == State.ALIAS_INPUT:
                        alias = parse_result.text
                        if not self.db.alias_exists(alias=alias):
                            self.send_message(peer_id=vk_id,
                                              message="Псевдоним ©{} успешно установлен.".format(alias),
                                              keyboard=Keyboard.BOT_MENU)
                            self.db.create_user(vk_id=vk_id, alias=alias)
                            self.db.set_user_state(vk_id=vk_id, state=State.BOT_MENU)
                        else:
                            raise BotRuntimeError(BotRuntimeError.ErrorCodes.ALIAS_ERROR, "alias already exists", True,
                                                  reply=ErrorPhrases.ALIAS_ALREADY_EXISTS.value)
                    else:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.STATE_ERROR,
                                              "unexpected state for unauthorized user", False)
                elif user_state in [State.QUOTE_CREATION_BM, State.QUOTE_CREATION_MQ]:
                    if len(event.message.attachments) > 1:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.ATTACHMENT_ERROR,
                                              "invalid amount of attachments", True,
                                              reply=ErrorPhrases.QUOTE_CREATION_ERROR_12.value,
                                              keyboard=Keyboard.FAQ_AND_RETURN)
                    if not (event.message.attachments[0].startswith('photo') or
                            event.message.attachments[0].startswith('music')):
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.ATTACHMENT_ERROR,
                                              "invalid type of attachment", True,
                                              reply=ErrorPhrases.QUOTE_CREATION_ERROR_13.value,
                                              keyboard=Keyboard.FAQ_AND_RETURN)
                    quote_id = self.db.create_quote(vk_id=vk_id, text=parse_result.text, tags=parse_result.tags,
                                                    author=parse_result.author, attachments=event.message.attachments)
                    saved_quote = self.get_quote(quote_id=quote_id)
                    reply = 'Высказывание сохранено:\n' + saved_quote[0]
                    self.send_message(peer_id=vk_id, message=reply, attachments=saved_quote[1],
                                      keyboard=Keyboard.FAQ_AND_RETURN)

                elif user_state in [State.SEARCH_BY_WORD, State.SEARCH_BY_TAG]:
                    print("SEARCH_BY: WORD / TAG")
                    if user_state == State.SEARCH_BY_WORD:
                        quotes = self.db.get_quotes_by_word(word_states=get_word_states(word=parse_result.text),
                                                            search_param=parse_result.search_param,
                                                            max_amount=SEARCH_QUOTES_AMOUNT)
                    else:
                        quotes = self.db.get_quotes_by_tag(tags=parse_result.tags,
                                                           search_param=parse_result.search_param,
                                                           max_amount=SEARCH_QUOTES_AMOUNT)
                    if quotes:
                        self.print_quote_list(vk_id=vk_id, quotes=quotes, keyboard=Keyboard.MY_QUOTES,
                                              print_quote_id=True)
                        self.send_message(peer_id=vk_id, keyboard=Keyboard.FAQ_AND_RETURN)
                    else:
                        self.send_message(peer_id=vk_id, message=GroupPhrases.SEARCH_EMPTY.value,
                                          keyboard=Keyboard.FAQ_AND_RETURN)

                elif user_state == State.ALIAS_CHANGING:
                    alias = parse_result.text
                    if not self.db.alias_exists(alias=alias):
                        self.send_message(peer_id=vk_id, message=GroupPhrases.ALIAS_CHANGED.value,
                                          keyboard=Keyboard.BOT_MENU)
                        self.db.set_user_alias(vk_id=vk_id, alias=alias)
                        self.db.set_user_state(vk_id=vk_id, state=State.BOT_MENU)
                    else:
                        raise BotRuntimeError(BotRuntimeError.ErrorCodes.ALIAS_ERROR, "alias already exists", True,
                                              reply=ErrorPhrases.ALIAS_ALREADY_EXISTS.value)

                else:
                    raise BotRuntimeError(BotRuntimeError.ErrorCodes.STATE_ERROR, "command not found", True,
                                          reply=ErrorPhrases.STATE_ERROR.value, keyboard=Keyboard.BOT_MENU)

            print(event.message['from_id'], event.message['text'])
        elif event.type == VkBotEventType.MESSAGE_REPLY:
            if event.object.text == GroupPhrases.GREETINGS.value:
                self.send_message(peer_id=event.object.from_id, message=GroupPhrases.ALIAS_INPUT.value)

    def parse_message(self, raw_message: str, state: State) -> ParseResult:
        message = raw_message.lower()
        print('msg:', message, 'state:', state)
        if message in [UserPhrases.START_RUS.value, UserPhrases.START_EN.value]:
            return self.ParseResult(True, command=Command.BOT_START)
        elif message == UserPhrases.CREATE_QUOTE.value:
            return self.ParseResult(True, command=Command.CREATE_QUOTE)
        elif message == UserPhrases.ADD_QUOTE.value:
            return self.ParseResult(True, command=Command.ADD_QUOTE)
        elif message == UserPhrases.DELETE_QUOTE.value:
            return self.ParseResult(True, command=Command.DELETE_QUOTE)
        elif message == UserPhrases.SEARCH_QUOTE.value:
            return self.ParseResult(True, command=Command.SEARCH_QUOTE)
        elif message == UserPhrases.SEARCH_BY_WORD.value:
            return self.ParseResult(True, command=Command.SEARCH_BY_WORD)
        elif message == UserPhrases.SEARCH_BY_TAG.value:
            return self.ParseResult(True, command=Command.SEARCH_BY_TAG)
        elif message == UserPhrases.MY_QUOTES.value:
            return self.ParseResult(True, command=Command.MY_QUOTES)
        elif message == UserPhrases.CHANGE_ALIAS.value:
            return self.ParseResult(True, command=Command.CHANGE_ALIAS)
        elif message == UserPhrases.FAQ.value:
            return self.ParseResult(True, command=Command.FAQ)
        elif message == UserPhrases.RETURN.value:
            return self.ParseResult(True, command=Command.RETURN)
        elif state in [State.QUOTE_CREATION_BM, State.QUOTE_CREATION_MQ]:
            if message[0] == '@':
                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, 'empty quote', True,
                                      reply=ErrorPhrases.QUOTE_CREATION_ERROR_1.value)
            else:
                splited = re.split(r'@', raw_message + ' ')
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
                        if author != '':
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

                return self.ParseResult(False, text=text, tags=tags, author=author, private=private)

        elif state in [State.SEARCH_BY_WORD, State.SEARCH_BY_TAG]:
            splited = re.split(r'@', raw_message)
            if len(splited) > 2:
                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "several args passed", True,
                                      reply=ErrorPhrases.SEARCH_ERROR_1.value)
            word = splited[0].strip()
            if state == State.SEARCH_BY_WORD and word.count(' '):
                raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "several words passed", True,
                                      reply=ErrorPhrases.SEARCH_ERROR_3.value)
            search_param = SearchParams.ALL
            if len(splited) == 2:
                param = splited[1].strip()
                if param in ['a', 'p']:
                    if param == 'a':
                        search_param = SearchParams.PUBLIC
                    else:
                        search_param = SearchParams.PRIVATE
                else:
                    raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "unknown param passed", True,
                                          reply=ErrorPhrases.SEARCH_ERROR_2.value)
            if state == State.SEARCH_BY_WORD:
                return self.ParseResult(False, text=word, search_param=search_param)
            else:
                return self.ParseResult(False, tags=word.split(), search_param=search_param)

        elif state in [State.ALIAS_CHANGING, State.ALIAS_INPUT]:
            alias = raw_message.strip()
            return self.ParseResult(False, text=alias)
        else:
            raise BotRuntimeError(BotRuntimeError.ErrorCodes.PARSE_ERROR, "unknown parse behavior", True,
                                  reply=ErrorPhrases.PARSE_UNKNOWN_BEHAVIOR.value)

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
