[![Build Status](https://travis-ci.org/uber/mutornadomon.png)](https://travis-ci.org/uber/mutornadomon)

**µtornadomon** is a library designed to be used with Tornado web applications. It adds an endpoint
(`/mutornadomon`) to HTTP servers which outputs application statistics for use with standard metric
collectors.

In general, to use it you do something like

```
from mutornadomon.config import initialize_mutornadomon
import signal

[...]

application = tornado.web.Application(...)
collector = initialize_mutornadomon(application)

def shut_down(*args):
    collector.stop()
    some_other_application_stop_function()
    tornado.ioloop.IOLoop.current().stop()

for sig in (signal.SIGQUIT, signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, shut_down)
```

If you want to add your own metrics, you can do so by calling the `.kv()` or
`.count()` methods on the collector object at any time.

The HTTP endpoint is restricted to only respond to request from loopback.
