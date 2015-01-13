import json

import tornado.testing
from mutornadomon.config import initialize_mutornadomon

from six import b


class HeloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('HELO %s' % self.request.remote_ip)


class TestBasic(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.app = tornado.web.Application([
            (r'/', HeloHandler)
        ])
        return self.app

    def setUp(self):
        super(TestBasic, self).setUp()
        self.monitor = initialize_mutornadomon(self.app)

    def tearDown(self):
        super(TestBasic, self).tearDown()
        self.monitor.stop()

    def test_endpoint(self):
        resp = self.fetch('/')
        self.assertEqual(resp.body, b('HELO 127.0.0.1'))
        resp = self.fetch('/mutornadomon')
        self.assertEqual(resp.code, 200)
        resp = json.loads(resp.body.decode('utf-8'))
        self.assertEqual(
            resp['counters'],
            {'requests': 2, 'localhost_requests': 2, 'private_requests': 2}
        )
        self.assertEqual(resp['process']['cpu']['num_threads'], 1)
        self.assertLess(resp['process']['cpu']['system_time'], 1)

    def test_endpoint_xff(self):
        resp = self.fetch('/mutornadomon', headers={'X-Forwarded-For': '127.0.0.2'})
        self.assertEqual(resp.code, 200)

    def test_endpoint_not_public(self):
        resp = self.fetch('/mutornadomon', headers={'X-Forwarded-For': '8.8.8.8'})
        self.assertEqual(resp.code, 403)
