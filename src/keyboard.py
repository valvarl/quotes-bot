# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from src.methods import BotRuntimeError, Keyboard


def create_keyboard(which: Keyboard) -> VkKeyboard:
    keyboard = VkKeyboard(one_time=True)

    if which == Keyboard.EMPTY:
        return keyboard.get_keyboard()

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
        keyboard.add_button("Поиск по тегу", color=VkKeyboardColor.PRIMARY)
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
