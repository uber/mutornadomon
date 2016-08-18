import time


class UtilizationCollector(object):
    """Collects stats for overall callback durations"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.monitor.profiler_init = False
        self.monitor.profiler_running = False
        self.monitor.profiler = None

    def start(self):
        self.original_run_callback = self.monitor.io_loop._run_callback
        self.original_add_handler = self.monitor.io_loop.add_handler

        def enable_profiler():
            """Enables profiler if required"""
            if not self.monitor.profiler_running:
                self.monitor.profiler.enable()
                self.monitor.profiler_running = True

        def update_callback_stats(start_time):
            """Update callback stats"""
            duration = (time.time() - start_time)
            self.monitor.count('callback_duration', duration)
            self.monitor.count('callbacks_processed', 1)

        def run_timed_callback(callback):
            if self.monitor.profiler_init:
                enable_profiler()

            start_time = time.time()
            result = self.original_run_callback(callback)
            update_callback_stats(start_time)

            return result

        def add_timed_handler(fd, handler, events):
            def timed_handler(*args, **kwargs):
                if self.monitor.profiler_init:
                    enable_profiler()

                start_time = time.time()
                result = handler(*args, **kwargs)
                update_callback_stats(start_time)

                return result

            self.original_add_handler(fd, timed_handler, events)

        self.monitor.io_loop.add_handler = add_timed_handler
        self.monitor.io_loop._run_callback = run_timed_callback

    def stop(self):
        self.monitor.io_loop._run_callback = self.original_run_callback
        self.monitor.io_loop.add_handler = self.original_add_handler
