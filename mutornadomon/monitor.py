from __future__ import absolute_import

import collections
import time

import tornado.ioloop
import tornado.web
import os
import psutil
import mock

from . import net

CALLBACK_FREQUENCY = 100  # ms


LOCALHOST = lambda request: net.is_local_address(request.remote_ip)


class StatusHandler(tornado.web.RequestHandler):
    def initialize(self, monitor, request_filter):
        self.monitor = monitor
        self.request_filter = request_filter

    def prepare(self):
        if not self.request_filter(self.request):
            self.send_error(403)

    def get(self):
        self.write(self.monitor.metrics)


class NullTransform(object):
    def transform_first_chunk(self, status_code, headers, chunk, *args, **kargs):
        return status_code, headers, chunk

    def transform_chunk(self, chunk):
        return chunk


class MuTornadoMon(object):
    def __init__(self, host_limit=r'.*', request_filter=LOCALHOST, io_loop=None):
        """Constructor for MuTornadoMon monitor

        :param host_limit: Regular expression of vhost to match, if you're
           using Tornado's vhosting stuff
        :param remote_client_filter: Function which, when called with the request
           will filter it. Defaults to a filter which only allows requests from
           127.0.0.0/8
        :param io_loop: IOLoop to run on if not using the standard singleton
        """
        if io_loop is None:
            io_loop = tornado.ioloop.IOLoop.current()
        self.io_loop = io_loop
        self._host_limit = host_limit
        self.request_filter = request_filter
        self.callback = tornado.ioloop.PeriodicCallback(self._cb, CALLBACK_FREQUENCY, self.io_loop)
        self._ioloop_exception_patch = None
        self._monkey_patch_ioloop_exceptions()
        self._COUNTERS = collections.Counter()
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
        self._last_cb_time = time.time()
        self.callback.start()

    def stop(self):
        if self.callback is not None:
            self.callback.stop()
            self.callback = None
        if self._ioloop_exception_patch is not None:
            self._ioloop_exception_patch.stop()

    def _cb(self):
        now = time.time()
        self.count('callbacks')
        latency = now - self._last_cb_time
        excess_latency = latency - (CALLBACK_FREQUENCY / 1000.0)
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
        meminfo = me.get_memory_info()
        cpuinfo = me.cpu_times()
        rv = {
            'process': {
                'uptime': time.time() - me.create_time(),
                'meminfo': {
                    'rss_bytes': meminfo.rss,
                    'vsz_bytes': meminfo.vms,
                },
                'cpu': {
                    'user_time': cpuinfo.user,
                    'system_time': cpuinfo.system,
                    'num_threads': me.num_threads(),
                }
            },
            'counters': dict(self._COUNTERS),
            'gauges': self._GAUGES,
            'max_gauges': self._MAX_GAUGES,
            'min_gauges': self._MIN_GAUGES,
        }
        self._reset_ephemeral()
        return rv

    def register_application(self, app):
        """Register an instance of tornado.web.Application to expose statistics on."""
        app.add_handlers(self._host_limit, [
            (r'/mutornadomon', StatusHandler, {
                'monitor': self,
                'request_filter': self.request_filter
            })
        ])
        self._instrument_app(app)

    def _request(self, request):
        self.count('requests', 1)
        if net.is_local_address(request.remote_ip):
            self.count('localhost_requests', 1)
        if net.is_private_address(request.remote_ip):
            self.count('private_requests', 1)
        return NullTransform()

    def _instrument_app(self, app):
        app.add_transform(self._request)
