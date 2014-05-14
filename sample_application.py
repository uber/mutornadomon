import signal

import tornado.web
import tornado.httpserver
import tornado.ioloop

import mutornadomon


def fail():
    assert False, 'oops'


class HeloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('HELO %s' % self.request.remote_ip)
        tornado.ioloop.IOLoop.current().add_callback(fail)


def main():
    application = tornado.web.Application([
        (r'/', HeloHandler)
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8080, '127.0.0.1')

    monitor = mutornadomon.MuTornadoMon()
    monitor.register_application(application)
    monitor.start()

    def stop(*args):
        print 'Good bye'
        monitor.stop()
        tornado.ioloop.IOLoop.current().stop()

    for sig in signal.SIGINT, signal.SIGQUIT, signal.SIGTERM:
        signal.signal(sig, stop)

    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
