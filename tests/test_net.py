from __future__ import absolute_import

import mock
import unittest

from mutornadomon.net import is_local_address
from mutornadomon.net import is_private_address


class TestIsLocalAddress(unittest.TestCase):

    @mock.patch('six.PY2')
    def test_is_local_address_works_with_python2(self, is_python2_mock):
        """Test is_local_address method works for python2."""
        is_python2_mock.return_value = True
        self.assertTrue(is_local_address(u'127.0.0.1'))
        self.assertTrue(is_local_address('127.0.0.1'))
        self.assertFalse(is_local_address('126.0.0.10'))

    @mock.patch('six.PY2')
    def test_is_local_address_works_with_python3(self, is_python2_mock):
        """Test is_local_address method works for python3."""
        is_python2_mock.return_value = False
        self.assertTrue(is_local_address(u'127.0.0.1'))
        self.assertTrue(is_local_address('127.0.0.1'))
        self.assertFalse(is_local_address('126.0.0.10'))


class TestIsPrivateAddress(unittest.TestCase):

    @mock.patch('six.PY2')
    def test_is_private_address_works_with_python2(self, is_python2_mock):
        """Test is_private_address method works for python2."""
        is_python2_mock.return_value = True
        self.assertTrue(is_private_address(u'127.0.0.1'))
        self.assertTrue(is_private_address('127.0.0.1'))
        self.assertFalse(is_private_address('126.0.0.10'))

    @mock.patch('six.PY2')
    def test_is_private_address_works_with_python3(self, is_python2_mock):
        """Test is_private_address method works for python3."""
        is_python2_mock.return_value = False
        self.assertTrue(is_private_address(u'127.0.0.1'))
        self.assertTrue(is_private_address('127.0.0.1'))
        self.assertFalse(is_private_address('126.0.0.10'))