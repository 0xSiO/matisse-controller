from queue import Queue


class LoggingStream:
    """A basic stream that is meant to replace sys.stdout."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, message):
        self.queue.put(message)
