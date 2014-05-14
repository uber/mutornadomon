**mutornadomon** is a library designed to be used with Tornado web applications. It adds an endpoint
(`/mutornadomon`) to HTTP servers which outputs application statistics for use with standard metric
collectors.

In general, to use it you do something like

```
import mutornadomon

[...]

application = tornado.web.Application(...)

collector = mutornadomon.MuTornadoMon()
collector.register_application(application)
collector.start()
```

If you want to add your own metrics, you can do so by calling the `.kv()` or
`.count()` methods on the collector object at any time.

The HTTP endpoint is restricted to only respond to request from loopback.
