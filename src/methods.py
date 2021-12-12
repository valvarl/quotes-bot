# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import pymorphy2
from enum import Enum


class State(Enum):
    ALIAS_INPUT = 0  # entering pseudonym
    BOT_MENU = 1  # bot main menu
    QUOTE_CREATION_BM = 2  # creating quote from bot menu
    QUOTE_CREATION_MQ = 3  # creating quote from my quotes
    QUOTE_SEARCH = 4  # searching quote
    MY_QUOTES = 5  # handling user's quotes
    ALIAS_CHANGING = 6  # changing of pseudonym
    QUOTE_ADDING = 7  # adding quote
    QUOTE_DELETING = 8  # deleting quote
    SEARCH_BY_TAG = 9  # searching by tag
    SEARCH_BY_WORD = 10  # searching by word


class SearchParams(Enum):
    PUBLIC = 0
    PRIVATE = 1
    ALL = 2


class Keyboard(Enum):
    BOT_MENU = 0            # bot main menu
    FAQ_AND_RETURN = 1      # faq and return buttons
    QUOTE_SEARCH = 2        # searching quote
    MY_QUOTES = 3           # handling user's quotes
    RETURN = 5              # only return button
    EMPTY = 6               # empty


class BotRuntimeError(Exception):
    class ErrorCodes(Enum):
        TYPE_ERROR = 0
        KEYBOARD_ERROR = 1
        COMMAND_ERROR = 2
        PARSE_ERROR = 3
        STATE_ERROR = 4
        ALIAS_ERROR = 5
        ATTACHMENT_ERROR = 6

    def __init__(self, code: ErrorCodes, what: str, need_reply: bool, *, reply='', keyboard=Keyboard.EMPTY):
        self.code = code
        self.what = what
        self.need_reply = need_reply
        self.reply = reply
        self.keyboard = keyboard


def check_args(args: dict):
    for variable_name, params in args.items():
        value, variable_type = params
        if type(value) != variable_type:
            what = "{} expected in {}".format(variable_type.__name__, variable_name)
            raise BotRuntimeError(BotRuntimeError.ErrorCodes.TYPE_ERROR.value, what, False)


# TODO: prepare word_states list using pymorphy2
def get_word_states(word: str) -> list:
    word_states = [word]
    return word_states


if __name__ == '__main__':
    print(get_word_states('бревно'))
    print(get_word_states('низвергнуть'))
    print(get_word_states('приходящий'))
    print(get_word_states('невпопад'))
    print(get_word_states('твой'))
    print(get_word_states('нашему'))
    print(get_word_states('оседлав'))
    print(get_word_states('полюбовно'))
    print(get_word_states('Валера'))
    print(get_word_states('прекрасный'))
    print(get_word_states('по-любому'))
    print(get_word_states('великолепен'))
