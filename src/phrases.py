# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum


class UserPhrases(Enum):
    START_RUS = "начать"
    START_EN = "start"
    CREATE_QUOTE = "создать цитату"
    DELETE_QUOTE = "удалить цитату"
    ADD_QUOTE = "добавить цитату"
    MY_QUOTES = "мои цитаты"
    CHANGE_ALIAS = "изменить псевдоним"
    SEARCH_BY_WORD = "поиск по слову"
    SEARCH_BY_TAG = "поиск по тэгу"
    FAQ = "справка"
    RETURN = "вернуться"


class GroupPhrases(Enum):
    GREETINGS = "Привет! В этом диалоге бот будет сохранять твои высказывания. Здесь ты можешь добавить свою цитату, " \
                "а также прочитать те, которыми поделились другие пользователи."
    ALIAS_INPUT = "Для начала придумай псевдоним. Им будут подписаны цитаты, которыми ты захочешь поделиться. " \
                  "Псевдоним всегда можно будет изменить."
    QUOTE_FAQ = "Чтобы добавить свою цитату, просто напиши ее (без кавычек). По умолчанию она будет подписана твоим " \
                "псевдонимом и будет доступна в поиске другим пользователям. Эти настройки можно изменить, " \
                "если после высказывания указать следующите параметры (в любом порядке):\n\n" \
                " @a Грибанов или @a \"Антон Чехов\" - изменить имя автора\n" \
                " @t тэг или @t \"тэг1 тэг2 тэг3\" - добавить тэги\n" \
                " @p - исключает высказывание из публичного поиска\n\n" \
                "Пример 1: высказывание <Сначала ищем на работе справедливость, потом другую работу. " \
                "@a \"русский народ\" @t работа> будет опубликовано публично за авторством \"русский народ\", " \
                "и может быть найдено по тэгу \"работа\"." \
                "Пример 2: высказывание <Нагнулся в душе за мылом, а сзади слышу... @p @a Леша> будет доступно " \
                "только тебе."
