from __future__ import absolute_import


from mutornadomon import MuTornadoMon
from mutornadomon.external_interfaces.publish import PublishExternalInterface
from mutornadomon.external_interfaces.http_endpoints import (
        HTTPEndpointExternalInterface, HTTPEndpointMuTornadoMonProfiler)
from mutornadomon.collectors.web import WebCollector
from mutornadomon.collectors.ioloop_util import UtilizationCollector


def initialize_mutornadomon(
                tornado_app=None, publisher=None, publish_interval=None,
                host_limit=None, request_filter=None, tracer_port=None,
                **monitor_config):
    """Register mutornadomon to get Tornado request metrics"""
    if not publisher and not tornado_app:
        raise ValueError(
                    'Must pass at least one of `publisher` and `tornado_app`')

    if publisher:
        external_interface = PublishExternalInterface(
                                publisher, publish_interval=publish_interval)
    else:
        external_interface = HTTPEndpointExternalInterface(
            tornado_app, request_filter=request_filter, host_limit=host_limit)

    # Start collecting metrics and register endpoint with app
    monitor = MuTornadoMon(external_interface, **monitor_config)
    monitor.start()

    # If tracer_port is not provided then don't start the profiler
    if tracer_port is not None:
        profiler_ep = HTTPEndpointMuTornadoMonProfiler(request_filter)
        profiler_ep.start(monitor, tracer_port)

    if tornado_app:
        web_collector = WebCollector(monitor, tornado_app)
        web_collector.start()

    utilization_collector = UtilizationCollector(monitor)
    utilization_collector.start()

    return monitor
