import time


class UtilizationCollector(object):

    def __init__(self, monitor):
        self.last_time = time.time()
        self.monitor = monitor

    def __enter__(self):
        now = time.time()
        self.last_time = now

    def __exit__(self, *args, **kwargs):
        duration = (time.time() - self.last_time)
        self.last_time = time.time()
        self.monitor.kv('callback_duration', duration)
        self.monitor.count('accumulated_callback_duration', duration)
