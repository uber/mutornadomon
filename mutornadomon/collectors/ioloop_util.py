import time
from functools import wraps


class UtilizationCollector(object):
    """Collects stats for overall callback durations"""

    def __init__(self, monitor):
        self.monitor = monitor

    def start(self):
        self.original_add_callback = self.monitor.io_loop.add_callback
        utilization_stat = ExecutionTimer(self.monitor)

        def measure_callback(callback):
            @wraps(callback)
            def timed_callback(*args, **kwargs):
                with utilization_stat:
                    return callback(*args, **kwargs)

            return timed_callback

        @wraps(self.original_add_callback)
        def add_timed_callback(callback, *args, **kwargs):
            return self.original_add_callback(measure_callback(callback), *args, **kwargs)

        self.monitor.io_loop.add_callback = add_timed_callback

    def stop(self):
        self.monitor.add_callback = self.original_add_callback


class ExecutionTimer(object):
    def __init__(self, monitor):
        self.last_start_time = time.time()
        self.monitor = monitor

    def __enter__(self):
        now = time.time()
        self.last_start_time = now

    def __exit__(self, *args, **kwargs):
        duration = (time.time() - self.last_start_time)
        self.last_start_time = time.time()
        self.monitor.kv('callback_duration', duration)
        self.monitor.count('accumulated_callback_duration', duration)
