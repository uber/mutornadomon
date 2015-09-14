[![Build Status](https://travis-ci.org/uber/mutornadomon.png)](https://travis-ci.org/uber/mutornadomon)
[![Coverage Status](https://coveralls.io/repos/uber/mutornadomon/badge.svg?branch=master&service=github)](https://coveralls.io/github/uber/mutornadomon?branch=master)

# mutornadomon

**µtornadomon** is a library designed to be used with Tornado web applications. It adds an endpoint
(`/mutornadomon`) to HTTP servers which outputs application statistics for use with standard metric
collectors.

# Usage

The monitor is initialized using `mutornadomon.config.initialize_mutornadomon`.

## Exposing an HTTP endpoint

If you only pass a tornado web application, it will include request/response statistics,
and expose an HTTP endpoint for polling by external processes:

```
from mutornadomon.config import initialize_mutornadomon
import signal

[...]

application = tornado.web.Application(...)
monitor = initialize_mutornadomon(application)

def shut_down(*args):
    monitor.stop()
    some_other_application_stop_function()
    tornado.ioloop.IOLoop.current().stop()

for sig in (signal.SIGQUIT, signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, shut_down)
```

This will add a `/mutornadomon` endpoint to the web application.

Here is an example request to that endpoint:

```
$ curl http://localhost:8080/mutornadomon
{"process": {"uptime": 38.98995113372803, "num_fds": 8, "meminfo": {"rss_bytes": 14020608, "vsz_bytes": 2530562048}, "cpu": {"num_threads": 1, "system_time": 0.049356776, "user_time": 0.182635456}}, "max_gauges": {"ioloop_pending_callbacks": 0, "ioloop_handlers": 2, "ioloop_excess_callback_latency": 0.0006290912628173773}, "min_gauges": {"ioloop_pending_callbacks": 0, "ioloop_handlers": 2, "ioloop_excess_callback_latency": -0.004179096221923834}, "gauges": {"ioloop_pending_callbacks": 0, "ioloop_handlers": 2, "ioloop_excess_callback_latency": 0.0006290912628173773}, "counters": {"callbacks": 388, "requests": 6, "localhost_requests": 6, "private_requests": 6}}
```

If you want to add your own metrics, you can do so by calling the `.kv()` or
`.count()` methods on the monitor object at any time.

The HTTP endpoint is restricted to only respond to request from loopback.

## Providing a publishing callback

Alternatively, instead of polling the HTTP interface, you can pass in a `publisher` callback:

```
import pprint

def publisher(metrics):
    pprint.pprint(metrics)

monitor = initialize_mutornadomon(application, publisher=publisher)
```

By default, this will call the publisher callback every 10 seconds.
To override this pass the `publish_interval` parameter (in miliseconds).

## Monitoring non-web applications

If you don't pass an application object, other stats can still be collected:

```
import pprint

def publisher(metrics):
    pprint.pprint(metrics)

monitor = initialize_mutornadomon(publisher=publisher)
```

This only works with the publisher callback interface.
