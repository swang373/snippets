import atexit
import os
import signal
import sys


class Daemon(object):
    """A basic daemon class. Credits to S. Marechal, the developers of daemonize and
    python-daemon, Python Cookbook 3rd Ed. by D. Beazley and B. Jones, and more.
    """
    def __init__(self, pidfile, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def start(self, *args, **kwargs):
        """Start the daemon.
        """
        # If a pidfile exists, the daemon could be running.
        if os.path.isfile(self.pidfile):
            raise RuntimeError('Already running.')
        # Daemonize the process and call the run method.
        self._daemonize()
        self.run(*args, **kwargs)

    def run(self):
        """Override this method when subclassing Daemon. It will be called
        after the process has been daemonized by start() or restart().
        """
        raise NotImplementedError

    def _daemonize(self):
        """Follow the standard UNIX double-fork procedure. Refer to W. Richard
        Stevens' "Advanced Programming in the UNIX Environment" for details.
        """
        # First fork to detach from the parent.
        try:
            pid = os.fork()
            if pid > 0:
                raise SystemExit(0)
        except OSError as e:
            raise RuntimeError('First fork failed: [{0.errno!s}] {0.strerror}'.format(e))
        # Ensure the daemon doesn't keep any directory in use and that
        # operating system calls provide their own permission masks.
        # The umask value of 022 is more secure than the standard 0.
        os.chdir('/')
        os.umask(022)
        os.setsid()
        # Second fork to relinquish session leadership.
        try:
            pid = os.fork()
            if pid > 0:
                raise SystemExit(0)
        except OSError as e:
            raise RuntimeError('Second fork failed: [{0.errno!s}] {0.strerror}'.format(e))
        # Flush I/O buffers and establish new file descriptors for the standard streams.
        sys.stdout.flush()
        sys.stderr.flush()
        stdin = file(self.stdin, 'r')
        stdout = file(self.stdout, 'a+')
        stderr = file(self.stderr, 'a+')
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())
        # Register the pidfile for removal upon exit.
        atexit.register(os.remove, self.pidfile)
        # Create the pidfile and write the daemon's PID.
        with open(self.pidfile, 'w') as pidfile:
            pidfile.write(str(os.getpid()))

