# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import pymorphy2


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
