import time


class UtilizationCollector(object):
    """Collects stats for overall callback durations"""

    def __init__(self, monitor):
        self.monitor = monitor

    def start(self):
        self.original_run_callback = self.monitor.io_loop._run_callback
        self.original_add_handler = self.monitor.io_loop.add_handler

        def run_timed_callback(callback):
            last_start_time = time.time()
            result = self.original_run_callback(callback)
            duration = (time.time() - last_start_time)
            self.monitor.count('callback_duration', duration)

            return result

        def add_timed_handler(fd, handler, events):
            def timed_handler(*args, **kwargs):
                start_time = time.time()
                result = handler(*args, **kwargs)
                duration = (time.time() - start_time)
                self.monitor.count('callback_duration', duration)

                return result

            self.original_add_handler(fd, timed_handler, events)

        self.monitor.io_loop.add_handler = add_timed_handler
        self.monitor.io_loop._run_callback = run_timed_callback

    def stop(self):
        self.monitor.io_loop._run_callback = self.original_run_callback
        self.monitor.io_loop.add_handler = self.original_add_handler
