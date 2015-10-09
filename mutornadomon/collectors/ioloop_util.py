import time
from functools import wraps


class UtilizationCollector(object):
    """Collects stats for overall callback durations"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.clear()

    def start(self):
        self.original_add_callback = self.monitor.io_loop.add_callback

        def measure_callback(callback):
            @wraps(callback)
            def timed_callback(*args, **kwargs):
                self.last_start_time = time.time()
                now = time.time()
                self.last_start_time = now
                result = callback(*args, **kwargs)
                duration = (time.time() - self.last_start_time)
                self.last_start_time = time.time()
                self.total_duration += duration
                self.callbacks += 1

                return result

            return timed_callback

        @wraps(self.original_add_callback)
        def add_timed_callback(callback, *args, **kwargs):
            return self.original_add_callback(measure_callback(callback), *args, **kwargs)

        self.monitor.io_loop.add_callback = add_timed_callback

    def stop(self):
        self.monitor.add_callback = self.original_add_callback

    def clear(self):
        self.total_duration = 0
        self.callbacks = 0
