from __future__ import absolute_import

from tornado.ioloop import IOLoop

from mutornadomon import MuTornadoMon
from mutornadomon.external_interfaces.publish import PublishExternalInterface
from mutornadomon.external_interfaces.http_endpoints import HTTPEndpointExternalInterface
from mutornadomon.collectors.web import WebCollector
from mutornadomon.collectors.ioloop_util import UtilizationCollector


def initialize_mutornadomon(tornado_app=None, publisher=None, publish_interval=None,
                            host_limit=None, request_filter=None, **monitor_config):
    """Register mutornadomon to get Tornado request metrics"""
    if not publisher and not tornado_app:
        raise ValueError('Must pass at least one of `publisher` and `tornado_app`')

    if publisher:
        external_interface = PublishExternalInterface(publisher,
                                                      publish_interval=publish_interval)
    else:
        external_interface = HTTPEndpointExternalInterface(tornado_app,
                                                           request_filter=request_filter,
                                                           host_limit=host_limit)

    # Start collecting metrics and register endpoint with app
    monitor = MuTornadoMon(external_interface, **monitor_config)
    monitor.start()

    ioloop = IOLoop.current()
    add_callback = ioloop.add_callback
    utilization_stat = UtilizationCollector(monitor)

    def measure_callback(callback):
        def timed_callback(*args, **kwargs):
            with utilization_stat:
                return callback(*args, **kwargs)

        return timed_callback

    def add_timed_callback(callback, *args, **kwargs):
        return add_callback(measure_callback(callback), *args, **kwargs)

    ioloop.add_callback = add_timed_callback

    if tornado_app:
        web_collector = WebCollector(monitor, tornado_app)
        web_collector.start()

    return monitor
