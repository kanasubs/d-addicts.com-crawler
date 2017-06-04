from unittest import TestCase

from lib.monad.either import *


class TopLevelTest(TestCase):
    def test_either(self):
        self.assertTrue(either(None), Left(None))
        self.assertTrue(either(4), Right(4))
        self.assertTrue(either(Left([])), Left([]))
        self.assertTrue(either(Right(4)), Right(4))
        for not_none_falsey in [0, [], {}, set(), ""]:
            self.assertTrue(isinstance(either(not_none_falsey), Right))
            self.assertTrue(isinstance(either(not_none_falsey, checker=bool), Left))


class LeftRightTest(TestCase):
    def test_or_call(self):
        self.assertEqual(Left(None).or_call(lambda x: x, 5), Right(5))
        self.assertEqual(Left(None).or_call(lambda x: x, None), Left(None))
        self.assertEqual(Right(6).or_call(lambda x: x, 5), Right(6))
        self.assertEqual(Right(6).or_call(lambda x: x, None), Right(6))

    def test_get_or(self):
        self.assertEqual(Left(None).get_or(5), Right(5))
        self.assertEqual(Left(None).get_or(None), Left(None))
        self.assertEqual(Left(None).get_or(Left(0)), Left(0))
        self.assertEqual(Right(6).get_or(5), Right(6))
        self.assertEqual(Right(6).get_or(None), Right(6))
