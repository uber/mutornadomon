import pprint
import signal
import sys

import tornado.web
import tornado.httpserver
import tornado.ioloop

from mutornadomon.config import initialize_mutornadomon, instrument_ioloop


def fail():
    assert False, 'oops'


class HeloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('HELO %s' % self.request.remote_ip)
        tornado.ioloop.IOLoop.current().add_callback(fail)


def publisher(metrics):
    print('Publishing metrics')
    pprint.pprint(metrics)


def main(active_publish=False):
    ioloop = tornado.ioloop.IOLoop.current()

    application = tornado.web.Application([
        (r'/', HeloHandler)
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8080, '127.0.0.1')

    if active_publish:
        monitor = instrument_ioloop(ioloop, publisher=publisher, publish_interval=1000)
    else:
        monitor = initialize_mutornadomon(application)

    def stop(*args):
        print('Good bye')
        monitor.stop()
        ioloop.stop()

    for sig in signal.SIGINT, signal.SIGQUIT, signal.SIGTERM:
        signal.signal(sig, stop)

    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main(active_publish='--active-publish' in sys.argv)
