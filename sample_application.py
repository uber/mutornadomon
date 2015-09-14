import pprint
import signal
import sys

import tornado.web
import tornado.httpserver
import tornado.ioloop

from mutornadomon.config import initialize_mutornadomon


def fail():
    assert False, 'oops'


class HeloHandler(tornado.web.RequestHandler):

    def get(self):
        self.write('HELO %s' % self.request.remote_ip)
        tornado.ioloop.IOLoop.current().add_callback(fail)


def publisher(metrics):
    print('Publishing metrics')
    pprint.pprint(metrics)


def main(publish=False, no_app=False):
    io_loop = tornado.ioloop.IOLoop.current()

    application = tornado.web.Application([
        (r'/', HeloHandler)
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8080, '127.0.0.1')

    if no_app:
        tornado_app = None
    else:
        tornado_app = application

    if publish:
        monitor = initialize_mutornadomon(tornado_app=tornado_app,
                                          io_loop=io_loop,
                                          publisher=publisher,
                                          publish_interval=5 * 1000)
    else:
        monitor = initialize_mutornadomon(tornado_app=tornado_app)

    def stop(*args):
        print('Good bye')
        monitor.stop()
        io_loop.stop()

    for sig in signal.SIGINT, signal.SIGQUIT, signal.SIGTERM:
        signal.signal(sig, stop)

    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main(publish='--publish' in sys.argv,
         no_app='--no-app' in sys.argv)
