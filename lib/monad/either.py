"""Source: https://github.com/kachayev/fn.py"""

from functools import partial
from operator import is_not

from pymonad.Either import Either, Left as PymonadLeft, Right as PymonadRight


def either(value, checker=partial(is_not, None)):
    if isinstance(value, Either):
        # either(Righty/Right) -> Right
        # either(Lefty/Left)   -> Left
        return value

    return Right(value) if checker(value) else Left(None)


class Left(PymonadLeft):
    def or_call(self, callback, *args, **kwargs):
        return either(callback(*args, **kwargs))

    def get_or(self, default):
        return either(default)


class Right(PymonadRight):
    def or_call(self, callback, *args, **kwargs):
        return self

    def get_or(self, default): return self
