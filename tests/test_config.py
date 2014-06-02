from __future__ import absolute_import

import mock
from mock import sentinel
import unittest

from mutornadomon.config import initialize_mutornadomon


class TestInitializeMutornadomon(unittest.TestCase):

    @mock.patch('mutornadomon.config.mutornadomon')
    def test_initialize_mutornadmon(self, mutornadomon_mock):
        """Test initialize_mutornadomon() setups monitoring and shutdown"""
        result = initialize_mutornadomon(sentinel.application,
                                         host_limit='test')
        monitor_inst = mutornadomon_mock.MuTornadoMon.return_value

        # initialize_mutornadomon() should return the monitor instance
        self.assertEqual(result, monitor_inst)

        # MuTornadoMon was created with monitor config values
        mutornadomon_mock.MuTornadoMon.assert_called_once_with(
            host_limit='test')

        # Monitor instance was registered with tornado application
        monitor_inst.register_application.assert_called_once_with(
            sentinel.application)
