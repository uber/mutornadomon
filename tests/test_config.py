from __future__ import absolute_import

import mock
from mock import sentinel
import mutornadomon
import tornado.ioloop
import unittest

from mutornadomon import MuTornadoMon
from mutornadomon.config import initialize_mutornadomon
from mutornadomon.external_interfaces import (HTTPEndpointExternalInterface,
                                              PublishExternalInterface)


class TestInitializeMutornadomon(unittest.TestCase):

    @mock.patch('mutornadomon.config.MuTornadoMon')
    @mock.patch('mutornadomon.config.WebCollector')
    @mock.patch('mutornadomon.config.UtilizationCollector')
    def test_initialize_mutornadmon(self, utilization_collector_mock, web_collector_mock, mutornadomon_mock):
        """Test initialize_mutornadomon() sets up HTTP endpoints interface"""
        app = sentinel.application,
        result = initialize_mutornadomon(app, host_limit='test')
        monitor_inst = mutornadomon_mock.return_value

        # initialize_mutornadomon() should return the monitor instance
        self.assertEqual(result, monitor_inst)

        assert mutornadomon_mock.call_count == 1
        web_collector_mock.assert_called_once_with(monitor_inst, app)
        utilization_collector_mock.assert_called_once_with(monitor_inst)

        # MuTornadoMon was created with monitor config values
        arg_list = mutornadomon_mock.call_args_list

        self.assertEquals(len(arg_list), 1)
        args, kwargs = arg_list[0]
        self.assertEqual(len(args), 1)
        self.assertTrue(isinstance(args[0], HTTPEndpointExternalInterface))

        self.assertEqual(kwargs, {})

    @mock.patch('mutornadomon.config.MuTornadoMon')
    @mock.patch('mutornadomon.config.WebCollector')
    @mock.patch('mutornadomon.config.UtilizationCollector')
    def test_initialize_mutornadmon_passes_publisher(
        self,
        utilization_collector_mock,
        web_collector_mock,
        mutornadomon_mock
    ):
        """Test initialize_mutornadomon() sets up publishing interface"""

        def publisher(monitor):
            pass

        app = sentinel.application
        result = initialize_mutornadomon(app,
                                         publisher=publisher,
                                         host_limit='test')
        monitor_inst = mutornadomon_mock.return_value

        # initialize_mutornadomon() should return the monitor instance
        self.assertEqual(result, monitor_inst)

        web_collector_mock.assert_called_once_with(monitor_inst, app)
        utilization_collector_mock.assert_called_once_with(monitor_inst)

        assert mutornadomon_mock.call_count == 1
        arg_list = mutornadomon_mock.call_args_list

        args, kwargs = arg_list[0]
        self.assertEqual(len(args), 1)
        self.assertTrue(isinstance(args[0], PublishExternalInterface))

        self.assertEqual(kwargs, {})

    @mock.patch('mutornadomon.config.MuTornadoMon')
    def test_initialize_mutornadmon_works_with_publisher_and_no_app(self, mutornadomon_mock):
        """Test initialize_mutornadomon() works with publisher, but no web app passed"""

        def publisher(monitor):
            pass

        monitor_inst = mutornadomon_mock.return_value
        result = initialize_mutornadomon(publisher=publisher)

        # initialize_mutornadomon() should return the monitor instance
        self.assertEqual(result, monitor_inst)

        assert mutornadomon_mock.call_count == 1

        # MuTornadoMon was created with monitor config values
        arg_list = mutornadomon_mock.call_args_list

        self.assertEquals(len(arg_list), 1)
        args, kwargs = arg_list[0]
        self.assertEqual(len(args), 1)
        self.assertTrue(isinstance(args[0], PublishExternalInterface))

        # No collectors are passed
        self.assertEqual(kwargs, {})

    @mock.patch('tornado.ioloop.PeriodicCallback')
    def test_publisher_initializer(self, periodic_callback_mock):
        """Test instrument_ioloop() setups monitoring and creates a PeriodicCallback"""

        def publisher():
            pass

        result = initialize_mutornadomon(io_loop=tornado.ioloop.IOLoop.current(), publisher=publisher)

        assert periodic_callback_mock.called

        self.assertTrue(isinstance(result, mutornadomon.MuTornadoMon))

    @mock.patch('tornado.ioloop.PeriodicCallback')
    def test_initialize_mutornadomon_raises_when_no_publisher_and_no_app(self, periodic_callback_mock):
        """Test instrument_ioloop() setups monitoring and creates a PeriodicCallback"""
        self.assertRaises(ValueError, initialize_mutornadomon,
                          io_loop=tornado.ioloop.IOLoop.current())

    @mock.patch('psutil.Process')
    @mock.patch('os.getpid')
    @mock.patch('mutornadomon.external_interfaces.PublishExternalInterface')
    def test_MuTornadoMon(self, pub_ext_iface_mock, mock_os, mock_ps):
        external_interface = pub_ext_iface_mock.return_value
        monitor = MuTornadoMon(external_interface)

        monitor.start()

        stat = 'test'
        val = 2

        # __COUNTERS[stat] = 2
        monitor.count(stat, val)

        # __COUNTERS[stat] = 3
        monitor.count(stat)
        self.assertEqual(monitor.metrics['counters'][stat], 3)


        monitor.kv(stat, 1)
        self.assertEqual(monitor.metrics['gauges'][stat], 1)

        # To make sure no exceptions are thrown
        monitor._cb()

        monitor.__del__()

    @mock.patch('tornado.ioloop')
    def test_initialize_PublishExternalInterface(self, mock_ioloop):

        def publisher(monitor):
            pass

        pub_inst = PublishExternalInterface(publisher=publisher)
        monitor = mock.MagicMock()
        pub_inst.start(monitor)
        self.assertTrue(pub_inst.publish_callback != None)

        self.assertRaises(ValueError, pub_inst.start, monitor=monitor)

        pub_inst._publish(monitor)

        pub_inst.stop()
        self.assertTrue(pub_inst.publish_callback == None)
