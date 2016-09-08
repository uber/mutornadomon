import tornado
import cProfile
import pstats
import time
from tornado import gen
import logging
from mutornadomon import net
from tornado.ioloop import IOLoop

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

logger = logging.getLogger('mutornadomon_profiler')


def LOCALHOST(request):
    if not net.is_local_address(request.remote_ip):
        return False
    xff = request.headers.get('X-Forwarded-For', None)
    if not xff or net.is_local_address(xff):
        return True
    return False


class HTTPEndpointMuTornadoMonProfiler(object):
    """Handles external HTTP requests for Profiler"""

    def __init__(self, request_filter):
        if request_filter is None:
            self.request_filter = LOCALHOST
        else:
            self.request_filter = request_filter

    def start(self, monitor, server_port):
        self.server_port = server_port
        self.profiler_app = tornado.web.Application([
            (r'/profiler', TornadoStatsHandler, {
                'monitor': monitor,
                'request_filter': self.request_filter
            }),
        ])

        # If listening is started directly then IOLoop started by service will
        # cause issue resulting in high CPU usage. So start listening after
        # IOLoop is started by the service
        io_loop = IOLoop.current(instance=False)
        if io_loop is None:
            logger.error('Cannot initialize Mutornadomon without IOLoop')
        else:
            io_loop.add_callback(self.start_listen)

    def start_listen(self):
        self.profiler_app.listen(self.server_port)
        logger.info('MuTornadoMon Profiler Listening on port %s',
                    self.server_port)

    def stop(self):
        pass


class TornadoStatsHandler(tornado.web.RequestHandler):
    """
    Profile Tornado IOLoop.
    Profiler will be started when the url end point is hit & stopped after
    profiletime or default profile collection time expires.
    waittime starts the profiling periodically, profiling is done for the
    duration of profiletime after waiting for a period of waittime.
    Params for the url are
    :param sortby: specifies how the profiling data will be sorted
        (ex: tottime or cumtime)
    :param profiletime: specifies how long profiling will be done (msec)
    :param waittime: specifies how long to wait when profiling periodically
    ex: curl "localhost:5951/profiler?sortby=cumtime&&profiletime=4000"
    ex: curl "localhost:5951/profiler?profiletime=200&&waittime=10000"
    """

    def initialize(self, monitor, request_filter):
        self.monitor = monitor
        self.request_filter = request_filter
        self.monitor.stop_profiler = False

    def prepare(self):
        if not self.request_filter(self.request):
            self.send_error(403)

    def print_profile_data(self, sortby, wait_time):
        ps = None
        # Stats fails if there is no profile data collected
        try:
            strm = StringIO()
            ps = pstats.Stats(self.monitor.profiler, stream=strm)
        except (TypeError, ValueError):
            self.write("No profiling data collected")
            return

        if ps is not None:
            ps.sort_stats(sortby)
            ps.print_stats()

            if wait_time == 0.0:
                self.write(strm.getvalue())
            else:
                logger.info(time.time())
                logger.info(strm.getvalue())

            self.monitor.profiler.clear()

    def set_options(self):
        valid_sortby = ['calls', 'cumulative', 'cumtime', 'file', 'filename',
                        'module', 'ncalls', 'pcalls', 'line', 'name', 'nfl',
                        'stdname', 'time', 'tottime']

        sortby = 'time'
        profile_time = 2.0
        wait_time = 0.0

        # Dictates how the profile data is sorted
        if 'sortby' in self.request.arguments:
            sortby = self.request.arguments['sortby'][0]

            if sortby not in valid_sortby:
                sortby = 'time'

        # profiletime(msec) indicates for how long each of the profiling is
        # done
        if 'profiletime' in self.request.arguments:
            profile_time = float(self.request.arguments['profiletime'][0])/1000

        # waittime(msec) indicates how long to wait between profiling
        if 'waittime' in self.request.arguments:
            wait_time = float(self.request.arguments['waittime'][0])/1000
            self.write("Profiling will be done for every " +
                       str(wait_time * 1000) + " msec\n")

        return sortby, profile_time, wait_time

    def disable_profiler(self):
        self.monitor.profiler_init = False
        self.monitor.profiler_running = False
        self.monitor.profiler.disable()

    @gen.coroutine
    def get(self):
        # Dictates whether to stop any on going profiling
        if 'stopprofiler' in self.request.arguments:
            self.monitor.profiler_init = False
            self.monitor.stop_profiler = True
            self.write("Stopped Profiling")
            return

        sortby, profile_time, wait_time = self.set_options()

        # If profiling is not started, start it
        if self.monitor.profiler_init is False:
            self.write("Profiling done for " + str(profile_time * 1000) +
                       " msec\n")
            if self.monitor.profiler is None:
                self.monitor.profiler = cProfile.Profile()
            else:
                self.monitor.profiler.clear()

        while True:
            # enable proflier for profile_time
            self.monitor.profiler_init = True
            yield gen.Task(self.monitor.io_loop.add_timeout,
                           time.time() + profile_time)

            # disable profiling
            self.disable_profiler()

            self.print_profile_data(sortby, wait_time)

            # Stop profiling for the duration of the wait_time
            yield gen.Task(self.monitor.io_loop.add_timeout,
                           time.time() + wait_time)

            # If wait_time is specified then continue profiling
            # All the profiling data  will be logged using the logger
            if ((wait_time == 0) or (self.monitor.stop_profiler is True)):
                break


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
    """External interface that exposes HTTP endpoints for polling by an
       external process.
    """

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
