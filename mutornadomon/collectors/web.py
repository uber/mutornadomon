from mutornadomon import net


class NullTransform(object):

    def transform_first_chunk(self, status_code, headers, chunk, *args, **kwargs):
        return status_code, headers, chunk

    def transform_chunk(self, chunk, *args, **kwargs):
        return chunk


class WebCollector(object):
    """Collects stats from a tornado.web.application.Application"""

    def __init__(self, monitor, tornado_app):
        self.monitor = monitor
        self.tornado_app = tornado_app

    def start(self):
        self.tornado_app.add_transform(self._request)

    def _request(self, request):
        self.monitor.count('requests', 1)
        if net.is_local_address(request.remote_ip):
            self.monitor.count('localhost_requests', 1)
        if net.is_private_address(request.remote_ip):
            self.monitor.count('private_requests', 1)
        return NullTransform()
