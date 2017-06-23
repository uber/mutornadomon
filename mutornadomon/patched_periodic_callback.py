from tornado.ioloop import PeriodicCallback


class PatchedPeriodicCallback(PeriodicCallback):
    def _run(self):
        if not self._running:
            return

        current_time = self.io_loop.time()
        if self._next_timeout > current_time:
            """ if called earlier """
            self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)
        else:
            try:
                return self.callback()
            except Exception:
                self.io_loop.handle_callback_exception(self.callback)
            finally:
                self._schedule_next()