# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from bot_base import BotRuntimeError


def check_args(args: dict):
    for variable_name, params in args.items():
        value, variable_type = params
        if type(value) != variable_type:
            what = "{} expected in {}".format(variable_type.__name__, variable_name)
            raise BotRuntimeError(BotRuntimeError.ErrorCodes.TYPE_ERROR.value, what, False)


# if __name__ == '__main__':
#     try:
#         check_args({'a': (1, int), 'b': ('12', str), 'c': ([], dict)})
#     except BotRuntimeError as e:
#         print(e.what)
