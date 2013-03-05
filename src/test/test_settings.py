'''
Tests for harmony.settings.
'''

import unittest
import harmony.settings as settings


class SettingTest(unittest.TestCase):
    setting_class = settings.Setting

    def setUp(self):
        self.s = self.__class__.setting_class()


class BaseSettingTest(SettingTest):
    setting_class = settings.Setting

    def test_validate(self):
        '''
        Test the validate() method. For the base Setting class, this should
        always return True.
        '''
        self.assertTrue(self.s.validate('foo'))
        self.assertTrue(self.s.validate(5))

    def test_transform(self):
        '''
        Test the transform() method. For the base Setting class, this should
        always return the passed in value.
        '''
        self.assertEqual(self.s.transform('foo'), 'foo')
        self.assertEqual(self.s.transform(5), 5)


class StringSettingTest(SettingTest):
    setting_class = settings.StringSetting

    def test_validate(self):
        '''StringSetting validates all string values as true.'''
        self.assertTrue(self.s.validate('foo'))
        self.assertTrue(self.s.validate(u'foo'))
        self.assertTrue(self.s.validate(bytes('foo')))

        self.assertFalse(self.s.validate(5))
        self.assertFalse(self.s.validate(True))

    def test_transform(self):
        '''StringSetting should transform all values to unicode strings.'''
        self.assertTrue(isinstance(self.s.transform('foo'), unicode))
        self.assertTrue(isinstance(self.s.transform(u'foo'), unicode))
        self.assertTrue(isinstance(self.s.transform(5), unicode))
        self.assertTrue(isinstance(self.s.transform(True), unicode))

        self.assertFalse(isinstance(self.s.transform('foo'), str))
        self.assertFalse(isinstance(self.s.transform(5), int))
        self.assertFalse(isinstance(self.s.transform(True), bool))


class TimezoneSettingTest(SettingTest):
    setting_class = settings.TimezoneSetting


class BooleanSettingTest(SettingTest):
    setting_class = settings.BooleanSetting

    def test_validate(self):
        '''
        BooleanSetting validates a predefined set of strings and other
        values as True. This is separate from the truthiness of the value
        itself.
        '''
        self.assertTrue(self.s.validate('yes'))
        self.assertTrue(self.s.validate('Yes'))
        self.assertTrue(self.s.validate('YES'))
        self.assertTrue(self.s.validate('true'))
        self.assertTrue(self.s.validate('True'))
        self.assertTrue(self.s.validate('TrUe'))
        self.assertTrue(self.s.validate('TRUE'))
        self.assertTrue(self.s.validate('1'))
        self.assertTrue(self.s.validate(1))
        self.assertTrue(self.s.validate(True))

        self.assertTrue(self.s.validate('no'))
        self.assertTrue(self.s.validate('false'))
        self.assertTrue(self.s.validate('NO'))
        self.assertTrue(self.s.validate('False'))
        self.assertTrue(self.s.validate('FaLse'))
        self.assertTrue(self.s.validate('FALSE'))
        self.assertTrue(self.s.validate('0'))
        self.assertTrue(self.s.validate(0))
        self.assertTrue(self.s.validate(False))

    def test_transform(self):
        '''
        BooleanSetting transforms values in the predefined set of true/false
        values into Python bools, and raises a ValueError for other values.
        '''
        self.assertTrue(self.s.transform('yes'))
        self.assertTrue(self.s.transform('Yes'))
        self.assertTrue(self.s.transform('YES'))
        self.assertTrue(self.s.transform('true'))
        self.assertTrue(self.s.transform('True'))
        self.assertTrue(self.s.transform('TrUe'))
        self.assertTrue(self.s.transform('TRUE'))
        self.assertTrue(self.s.transform('1'))
        self.assertTrue(self.s.transform(1))
        self.assertTrue(self.s.transform(True))

        self.assertEqual(self.s.transform('no'), False)
        self.assertEqual(self.s.transform('false'), False)
        self.assertEqual(self.s.transform('NO'), False)
        self.assertEqual(self.s.transform('False'), False)
        self.assertEqual(self.s.transform('FaLse'), False)
        self.assertEqual(self.s.transform('FALSE'), False)
        self.assertEqual(self.s.transform('0'), False)
        self.assertEqual(self.s.transform(0), False)
        self.assertEqual(self.s.transform(False), False)

        self.assertRaises(ValueError, self.s.transform, 'foo')
        self.assertRaises(ValueError, self.s.transform, 5)
        self.assertRaises(ValueError, self.s.transform, '5')
