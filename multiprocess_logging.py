import logging
import multiprocessing
import Queue
import threading


# Probably not a good idea to mix processes with threads due to Python Issue 6721
# We've even run into it at CERN:
# https://twiki.cern.ch/twiki/bin/view/Main/PythonLoggingThreadingMultiprocessingIntermixedStudy

class MultiprocessStreamHandler(logging.StreamHandler):
    """A subclass of StreamHandler which synchronizes record logging using a queue.
    """
    def __init__(self, *args, **kwargs):
        super(MultiprocessStreamHandler, self).__init__(*args, **kwargs)
        self.record_queue = multiprocessing.Queue(-1)
        receiving_thread = threading.Thread(target = self.receive)
        receiving_thread.daemon = True
        receiving_thread.start()

    def emit(self, record):
        try:
            self.record_queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def receive(self):
         while True:
            try:
                record = self.record_queue.get()
                logging.StreamHandler.emit(self, record)
            except Queue.Empty:
                pass
            except (KeyboardInterrupt, SystemExit):
                raise

class MultiprocessFileHandler(logging.FileHandler):
    """A subclass of FileHandler which synchronizes record logging using a queue.
    """
    def __init__(self, *args, **kwargs):
        super(MultiprocessFileHandler, self).__init__(*args, **kwargs)
        self.record_queue = multiprocessing.Queue(-1)
        receiving_thread = threading.Thread(target = self.receive)
        receiving_thread.daemon = True
        receiving_thread.start()

    def emit(self, record):
        try:
            self.record_queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def receive(self):
        while True:
            try:
                record = self.record_queue.get()
                logging.FileHandler.emit(self, record)
            except Queue.Empty:
                pass
            except (KeyboardInterrupt, SystemExit):
                raise

