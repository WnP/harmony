'''
Test cases for harmony.remote.dav.
'''

import unittest
import harmony.remote.dav as dav


class TestCalDAVClient(unittest.TestCase):
    pass


class TestRootParser(unittest.TestCase):
    def setUp(self):
        self.parser = dav.RootParser()

    def test_positive_namespace_split(self):
        ns, tag = self.parser._split_namespace('caldav:calendar')
        self.assertTrue(ns == 'caldav')
        self.assertTrue(tag == 'calendar')

        ns, tag = self.parser._split_namespace('foo')
        self.assertTrue(ns == '')
        self.assertTrue(tag == 'foo')
