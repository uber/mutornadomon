from __future__ import absolute_import

import mutornadomon


def initialize_mutornadomon(tornado_app, **monitor_config):
    """Register mutornadomon to get Tornado request metrics"""
    # Start collecting metrics and register endpoint with app
    monitor = mutornadomon.MuTornadoMon(**monitor_config)
    monitor.register_application(tornado_app)
    monitor.start()
    return monitor


def instrument_ioloop(io_loop, publisher, **monitor_config):
    monitor = mutornadomon.MuTornadoMon(io_loop=io_loop, publisher=publisher, **monitor_config)
    monitor.start()
    return monitor
