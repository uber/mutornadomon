import time
from functools import wraps


class UtilizationCollector(object):
    """Collects stats for overall callback durations"""

    def __init__(self, monitor):
        self.monitor = monitor

    def start(self):
        self.original_add_callback = self.monitor.io_loop.add_callback

        def measure_callback(callback):
            @wraps(callback)
            def timed_callback(*args, **kwargs):
                last_start_time = time.time()
                result = callback(*args, **kwargs)
                duration = (time.time() - last_start_time)
                self.monitor.accumulated_kv('callback_duration', duration)

                return result

            return timed_callback

        @wraps(self.original_add_callback)
        def add_timed_callback(callback, *args, **kwargs):
            return self.original_add_callback(measure_callback(callback), *args, **kwargs)

        self.monitor.io_loop.add_callback = add_timed_callback

    def stop(self):
        self.monitor.add_callback = self.original_add_callback
