import tornado
import cProfile
import pstats
import time
from tornado import gen
import logging
from mutornadomon import net

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

logger = logging.getLogger('mutornadomon')


def LOCALHOST(request):
    if not net.is_local_address(request.remote_ip):
        return False
    xff = request.headers.get('X-Forwarded-For', None)
    if not xff or net.is_local_address(xff):
        return True
    return False


class HTTPEndpointMuTornadoMonTracer(object):
    """Handles external HTTP requests for tracer"""

    def __init__(self, monitor, request_filter, server_port):

        if request_filter is None:
            self.request_filter = LOCALHOST
        else:
            self.request_filter = request_filter

        self.tracer_app = tornado.web.Application([
            (r'/', TornadoStatsHandler, {
                'monitor': monitor,
                'request_filter': self.request_filter
                }),
            ])

        self.tracer_app.listen(server_port)
        logger.info('MuTornadoMon Tracer Listening on port %s', server_port)

    def start(self):
        pass

    def stop(self):
        pass


class TornadoStatsHandler(tornado.web.RequestHandler):
    """
    Start & return the Tornado IOLoop stack trace.
    Tracing will be started when the url end point is hit & stopped after
    waittime or default trace collection time expires
    Params for the url are
    :param sortby: specifies how the traces will be sorted
        (ex: tottime or cumtime)
    :param waittime: specifies how long the traces will be collected (msec)

    ex: curl "localhost:5951/?sortby=cumtime&&waittime=4000"
    """

    def initialize(self, monitor, request_filter):
        self.monitor = monitor
        self.request_filter = request_filter

    def prepare(self):
        if not self.request_filter(self.request):
            self.send_error(403)

    @gen.coroutine
    def get(self):
        valid_sortby = ['calls', 'cumulative', 'cumtime', 'file', 'filename', 'module',
                        'ncalls', 'pcalls', 'line', 'name', 'nfl', 'stdname', 'time', 'tottime']

        sortby = 'time'
        wait_time = 3.0

        # Dictates how the stack trace is sorted
        if 'sortby' in self.request.arguments:
            sortby = self.request.arguments['sortby'][0]

            if sortby not in valid_sortby:
                sortby = 'time'

        # Wait time(msec) indicates for how long the trace is collected
        if 'waittime' in self.request.arguments:
            wait_time = float(self.request.arguments['waittime'][0])/1000

        # If collecting trace is not started, start it
        if self.monitor.stats_init is False:
            self.write("Trace collected for " + str(wait_time * 1000) + " msec\n")
            self.monitor.stats_init = True
            self.monitor.profiler = cProfile.Profile()
            yield gen.Task(self.monitor.io_loop.add_timeout, time.time() + wait_time)

        # disable collecting trace
        self.monitor.stats_init = False

        # Stats fails if there is no trace collected
        try:
            strm = StringIO()
            ps = pstats.Stats(self.monitor.profiler, stream=strm)
        except TypeError:
            self.write("No trace collected")
            return

        if ps is not None:
            ps.sort_stats(sortby)
            ps.print_stats()
            self.write(strm.getvalue())


class StatusHandler(tornado.web.RequestHandler):

    def initialize(self, monitor, request_filter):
        self.monitor = monitor
        self.request_filter = request_filter

    def prepare(self):
        if not self.request_filter(self.request):
            self.send_error(403)

    def get(self):
        self.write(self.monitor.metrics)


class HTTPEndpointExternalInterface(object):
    """External interface that exposes HTTP endpoints for polling by an external process."""

    def __init__(self, app, host_limit=None, request_filter=None):
        self.app = app
        if request_filter is None:
            self.request_filter = LOCALHOST
        else:
            self.request_filter = request_filter

        if host_limit is None:
            self._host_limit = r'.*'
        else:
            self._host_limit = host_limit

    def start(self, monitor):
        self.app.add_handlers(self._host_limit, [
            (r'/mutornadomon', StatusHandler, {
                'monitor': monitor,
                'request_filter': self.request_filter
            })
        ])

    def stop(self):
        pass
