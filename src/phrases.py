# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum


class Phrases(Enum):
    GREETINGS = "Привет! В этом диалоге бот будет сохранять твои высказывания. Здесь ты можешь добавить свою цитату, " \
                "а также прочитать те, которыми поделились другие пользователи."
    START_RUS = "начать"
    START_EN = "start"
