import tornado

from mutornadomon import net


def LOCALHOST(request):
    if not net.is_local_address(request.remote_ip):
        return False
    xff = request.headers.get('X-Forwarded-For', None)
    if not xff or net.is_local_address(xff):
        return True
    return False


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
