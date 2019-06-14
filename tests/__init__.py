
# Native libraries
# noinspection PyUnresolvedReferences
import unittest

# Tests
from .test_sqlite import TestSqlite
from .test_mongodb import TestMongoDB


def run_all_tests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite
