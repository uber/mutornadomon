import time


class UtilizationCollector(object):
    """Collects stats for overall callback durations"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.monitor.stats_init = False

    def start(self):
        self.original_run_callback = self.monitor.io_loop._run_callback
        self.original_add_handler = self.monitor.io_loop.add_handler

        def enable_profiler():
            """Enables profiler if required & returns current time"""
            profiler_enabled = False

            if self.monitor.stats_init:
                self.monitor.profiler.enable()
                profiler_enabled = True

            return profiler_enabled, time.time()

        def disable_profiler(profiler_enabled, start_time):
            """Disables profiler & updates callback duration"""
            if profiler_enabled:
                self.monitor.profiler.disable()

            duration = (time.time() - start_time)
            self.monitor.count('callback_duration', duration)
            self.monitor.count('callbacks_processed', 1)

        def run_timed_callback(callback):

            profiler_enabled, start_time = enable_profiler()
            result = self.original_run_callback(callback)
            disable_profiler(profiler_enabled, start_time)

            return result

        def add_timed_handler(fd, handler, events):
            def timed_handler(*args, **kwargs):

                profiler_enabled, start_time = enable_profiler()
                result = handler(*args, **kwargs)
                disable_profiler(profiler_enabled, start_time)

                return result

            self.original_add_handler(fd, timed_handler, events)

        self.monitor.io_loop.add_handler = add_timed_handler
        self.monitor.io_loop._run_callback = run_timed_callback

    def stop(self):
        self.monitor.io_loop._run_callback = self.original_run_callback
        self.monitor.io_loop.add_handler = self.original_add_handler
