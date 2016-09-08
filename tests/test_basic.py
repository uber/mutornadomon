import json

import mock
import psutil
from tornado.ioloop import IOLoop
import tornado.testing
from mutornadomon.config import initialize_mutornadomon
from tornado.httpclient import AsyncHTTPClient
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

    @mock.patch.object(psutil.Process, 'num_threads', autospec=True, return_value=5)
    def test_endpoint(self, mock_num_threads):
        resp = self.fetch('/')
        self.assertEqual(resp.body, b('HELO 127.0.0.1'))
        resp = self.fetch('/mutornadomon')
        self.assertEqual(resp.code, 200)
        resp = json.loads(resp.body.decode('utf-8'))
        expected = {'requests': 2, 'localhost_requests': 2, 'private_requests': 2}.items()
        self.assertTrue(all(pair in resp['counters'].items() for pair in expected))
        self.assertEqual(resp['process']['cpu']['num_threads'], 5)
        assert resp['process']['cpu']['system_time'] < 1.0

    def test_endpoint_xff(self):
        resp = self.fetch('/mutornadomon', headers={'X-Forwarded-For': '127.0.0.2'})
        self.assertEqual(resp.code, 200)

    def test_endpoint_not_public(self):
        resp = self.fetch('/mutornadomon', headers={'X-Forwarded-For': '8.8.8.8'})
        self.assertEqual(resp.code, 403)


class TestPublisher(tornado.testing.AsyncTestCase):

    @mock.patch.object(psutil.Process, 'num_threads', autospec=True, return_value=5)
    def test_publisher_called(self, mock_num_threads):
        publisher = mock.Mock(return_value=None)

        monitor = initialize_mutornadomon(io_loop=IOLoop.current(), publisher=publisher)
        monitor.count('my_counter', 2)
        monitor.external_interface._publish(monitor)

        self.assertTrue(publisher.called_once())
        metrics = publisher.call_args_list[0][0][0]

        self.assertEqual(
            metrics['counters'],
            {'my_counter': 2}
        )
        self.assertEqual(metrics['process']['cpu']['num_threads'], 5)
        assert metrics['process']['cpu']['system_time'] < 1.0


class TestProfiler(tornado.testing.AsyncTestCase):

    def setUp(self):
        super(TestProfiler, self).setUp()
        self.publisher = mock.Mock(return_value=None)
        self.io_loop = IOLoop.current()
        self.monitor = initialize_mutornadomon(
            io_loop=self.io_loop, publisher=self.publisher, tracer_port=5989)

    def tearDown(self):
        super(TestProfiler, self).tearDown()
        self.monitor.stop()

    @tornado.testing.gen_test
    @mock.patch.object(psutil.Process, 'num_threads',
                       autospec=True, return_value=5)
    def test_profiler_endpoint(self, mock_num_threads):
        client = AsyncHTTPClient(self.io_loop)
        resp = yield client.fetch("http://localhost:5989/profiler")

        profile_str = "Profiling done for"
        self.assertTrue(profile_str in str(resp.body))

    @tornado.testing.gen_test
    def test_profiler_endpoint_params(self):
        client = AsyncHTTPClient(self.io_loop)
        resp = yield client.fetch(
            "http://localhost:5989/profiler?sortby=cumulative&&profiletime=200")

        profile_str = "Profiling done for"
        self.assertTrue(profile_str in str(resp.body),
                        msg='{0}'.format(str(resp.body)))

    @tornado.testing.gen_test
    def test_profiler_endpoint_invalid_param(self):
        client = AsyncHTTPClient(self.io_loop)
        resp = yield client.fetch(
            "http://localhost:5989/profiler?sortby=badparam&&profiletime=200")

        profile_str = "Profiling done for"
        self.assertTrue(profile_str in str(resp.body),
                        msg='{0}'.format(str(resp.body)))

    @tornado.testing.gen_test
    def test_profiler_endpoint_periodic(self):
        client = AsyncHTTPClient(self.io_loop)
        resp = yield client.fetch("http://localhost:5989/profiler?stopprofiler")

        profile_str = "Stopped Profiling"
        self.assertTrue(profile_str in str(resp.body),
                        msg='{0}'.format(str(resp.body)))
