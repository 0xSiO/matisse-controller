from queue import Queue


class LoggingStream:
    """A basic stream-like class with a message queue, meant to replace sys.stdout for logging purposes."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, message):
        self.queue.put(message)

    def flush(self):
        pass
