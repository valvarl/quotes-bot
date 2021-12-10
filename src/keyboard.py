# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from src.bot_base import BotRuntimeError


class Keyboard(Enum):
    BOT_MENU = 0            # bot main menu
    FAQ_AND_RETURN = 1      # faq and return buttons
    QUOTE_SEARCH = 2        # searching quote
    MY_QUOTES = 3           # handling user's quotes
    RETURN = 5              # only return button
    EMPTY = 6               # empty


def create_keyboard(which: Keyboard) -> VkKeyboard:
    keyboard = VkKeyboard(one_time=True)

    if which == Keyboard.BOT_MENU:
        keyboard.add_button("Создать цитату", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Найти цитату", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("Мои цитаты", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Изменить псевдоним", color=VkKeyboardColor.PRIMARY)

    elif which == Keyboard.FAQ_AND_RETURN:
        keyboard.add_button("Справка", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Вернуться", color=VkKeyboardColor.PRIMARY)

    elif which == Keyboard.QUOTE_SEARCH:
        keyboard.add_button("Поиск по слову", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Поиск по тэгу", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("Случайный поиск", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Вернуться", color=VkKeyboardColor.PRIMARY)

    elif which == Keyboard.MY_QUOTES:
        keyboard.add_button("Добавить цитату", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Удалить цитату", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("Сохранить цитату", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Вернуться", color=VkKeyboardColor.PRIMARY)

    elif which == Keyboard.RETURN:
        keyboard.add_button("Вернуться", color=VkKeyboardColor.PRIMARY)

    else:
        raise BotRuntimeError(BotRuntimeError.ErrorCodes.KEYBOARD_ERROR, 'unknown keyboard requested', False)

    keyboard = keyboard.get_keyboard()
    return keyboard
