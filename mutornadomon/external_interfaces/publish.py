import logging

import tornado


class PublishExternalInterface(object):
    """External interface that delegates metrics publishing to a publisher callback."""
    PUBLISH_FREQUENCY = 10 * 1000  # ms

    logger = logging.getLogger('mutornadomon')

    def __init__(self, publisher, publish_interval=None):
        self.publisher = publisher
        self.publish_callback = None
        self.publish_interval = publish_interval or self.PUBLISH_FREQUENCY

    def start(self, monitor):
        if self.publish_callback is not None:
            raise ValueError('Publish callback already started')

        self.publish_callback = tornado.ioloop.PeriodicCallback(
            lambda: self._publish(monitor),
            self.publish_interval,
            monitor.io_loop,
        )
        self.publish_callback.start()

    def stop(self):
        if self.publish_callback is not None:
            self.publish_callback.stop()
            self.publish_callback = None

    def _publish(self, monitor):
        try:
            self.publisher(monitor.metrics)
        except:
            self.logger.exception('Metrics publisher raised an exception')
