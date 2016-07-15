from __future__ import absolute_import

import collections
import time

import tornado.ioloop
import tornado.web
import os
import psutil
import mock

CALLBACK_FREQUENCY = 100  # ms


class MuTornadoMon(object):

    def __init__(
        self,
        external_interface,
        collectors=None,
        io_loop=None,
        measure_interval=CALLBACK_FREQUENCY,
    ):
        """Constructor for MuTornadoMon monitor

        :param host_limit: Regular expression of vhost to match, if you're
           using Tornado's vhosting stuff.

        :param remote_client_filter: Function which, when called with the request
           will filter it. Defaults to a filter which only allows requests from
           127.0.0.0/8.

        :param io_loop: IOLoop to run on if not using the standard singleton.

        :param external_interface:

        :param measure_interval: The interval at which the latency of the ioloop is measured.
        """
        if collectors is None:
            self.collectors = []
        else:
            self.collectors = collectors
        self.io_loop = io_loop or tornado.ioloop.IOLoop.current()

        self.measure_interval = measure_interval

        self.measure_callback = tornado.ioloop.PeriodicCallback(
            self._cb,
            measure_interval,
            self.io_loop,
        )

        self.external_interface = external_interface

        self._ioloop_exception_patch = None
        self._monkey_patch_ioloop_exceptions()
        if hasattr(collections, 'Counter'):
            self._COUNTERS = collections.Counter()
        else:
            self._COUNTERS = collections.defaultdict(lambda: 0)
        self._GAUGES = {}
        self._reset_ephemeral()

    def _monkey_patch_ioloop_exceptions(self):
        if self._ioloop_exception_patch is not None:
            return

        _original_handler = self.io_loop.handle_callback_exception

        def handle_callback_exception(*args, **kwargs):
            self.count('unhandled_exceptions', 1)
            _original_handler(*args, **kwargs)

        self._ioloop_exception_patch = mock.patch.object(
            self.io_loop,
            'handle_callback_exception',
            handle_callback_exception
        )
        self._ioloop_exception_patch.start()

    def __del__(self):
        self.stop()

    def _reset_ephemeral(self):
        """Reset ephemeral statistics.

        For some things, rather than recording all values or just the latest
        value, we want to record the highest or lowest value since the last
        time stats were sampled. This function resets those gauges.
        """
        self._MIN_GAUGES = {}
        self._MAX_GAUGES = {}

    def count(self, stat, value=1):
        """Increment a counter by the given value"""
        self._COUNTERS[stat] += value

    def kv(self, stat, value):
        """Set a gauge to the given stat and value.

        The monitor also keeps track of the max and min value seen between subsequent calls
        to the .metrics property.
        """
        self._GAUGES[stat] = value
        if stat not in self._MAX_GAUGES or value > self._MAX_GAUGES[stat]:
            self._MAX_GAUGES[stat] = value
        if stat not in self._MIN_GAUGES or value < self._MIN_GAUGES[stat]:
            self._MIN_GAUGES[stat] = value

    def start(self):
        for collector in self.collectors:
            collector.start(self)
        self.external_interface.start(self)
        self._last_cb_time = time.time()
        self.measure_callback.start()

    def stop(self):
        self.external_interface.stop()
        for collector in self.collectors:
            collector.stop()
        if self.measure_callback is not None:
            self.measure_callback.stop()
            self.measure_callback = None
        if self._ioloop_exception_patch is not None:
            self._ioloop_exception_patch.stop()
            self._ioloop_exception_patch = None

    def _cb(self):
        now = time.time()
        self.count('callbacks')
        latency = now - self._last_cb_time
        excess_latency = latency - (self.measure_interval / 1000.0)
        self._last_cb_time = now
        self.kv('ioloop_excess_callback_latency', excess_latency)
        if hasattr(self.io_loop, '_handlers'):
            self.kv('ioloop_handlers', len(self.io_loop._handlers))
        if hasattr(self.io_loop, '_callbacks'):
            self.kv('ioloop_pending_callbacks', len(self.io_loop._callbacks))

    @property
    def metrics(self):
        """Return the current metrics. Resets max gauges."""
        me = psutil.Process(os.getpid())

        # Starting with 2.0.0, get_* methods are deprecated.
        # At 3.1.1 they are dropped.
        if psutil.version_info < (2, 0, 0):
            meminfo = me.get_memory_info()
            cpuinfo = me.get_cpu_times()
            create_time = me.create_time
            num_threads = me.get_num_threads()
            num_fds = me.get_num_fds()
        else:
            meminfo = me.memory_info()
            cpuinfo = me.cpu_times()
            create_time = me.create_time()
            num_threads = me.num_threads()
            num_fds = me.num_fds()
        rv = {
            'process': {
                'uptime': time.time() - create_time,
                'meminfo': {
                    'rss_bytes': meminfo.rss,
                    'vsz_bytes': meminfo.vms,
                },
                'cpu': {
                    'user_time': cpuinfo.user,
                    'system_time': cpuinfo.system,
                    'num_threads': num_threads,
                },
                'num_fds': num_fds
            },
            'counters': dict(self._COUNTERS),
            'gauges': self._GAUGES,
            'max_gauges': self._MAX_GAUGES,
            'min_gauges': self._MIN_GAUGES,
        }
        self._reset_ephemeral()
        return rv
