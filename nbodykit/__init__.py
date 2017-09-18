from .version import __version__

from mpi4py import MPI

# prevents too many threads exception when using MPI and dask
import dask
dask.set_options(get=dask.get)

_global_options = {}
_global_options['dask_cache_size'] = 1e9
_global_options['dask_chunk_size'] = int(5e6)

class set_options(object):
    """
    Set global configuration options.

    Parameters
    ----------
    dask_chunk_size : int
        the number of elements for the default chunk size for dask arrays;
        chunks should usually hold between 10 MB and 100 MB
    dask_cache_size : float
        the size of the internal dask cache in bytes; default is 1e9
    """
    def __init__(self, **kwargs):
        self.old = _global_options.copy()
        _global_options.update(kwargs)

    def __enter__(self):
        return

    def __exit__(self, type, value, traceback):
        _global_options.clear()
        _global_options.update(self.old)

class CurrentMPIComm(object):
    """
    A class to faciliate getting and setting the current MPI communicator.
    """
    _instance = None

    @staticmethod
    def enable(func):
        """
        Decorator to attach the current MPI communicator to the input
        keyword arguments of ``func``, via the ``comm`` keyword.
        """
        import functools
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            kwargs.setdefault('comm', None)
            if kwargs['comm'] is None:
                kwargs['comm'] = CurrentMPIComm.get()
            return func(*args, **kwargs)
        return wrapped

    @classmethod
    def get(cls):
        """
        Get the current MPI communicator, returning ``MPI.COMM_WORLD``
        if it has not be explicitly set yet.
        """
        # initialize MPI and set the comm if we need to
        if not cls._instance:
            comm = MPI.COMM_WORLD
            cls._instance = comm

        return cls._instance

    @classmethod
    def set(cls, comm):
        """
        Set the current MPI communicator to the input value.
        """
        cls._instance = comm

_logging_handler = None
def setup_logging(log_level="info"):
    """
    Turn on logging, with the specified level.

    Parameters
    ----------
    log_level : 'info', 'debug', 'warning'
        the logging level to set; logging below this level is ignored
    """

    # This gives:
    #
    # [ 000000.43 ]   0: 06-28 14:49  measurestats    INFO     Nproc = [2, 1, 1]
    # [ 000000.43 ]   0: 06-28 14:49  measurestats    INFO     Rmax = 120
    import logging

    levels = {
            "info" : logging.INFO,
            "debug" : logging.DEBUG,
            "warning" : logging.WARNING,
            }

    import time
    logger = logging.getLogger();
    t0 = time.time()

    rank = MPI.COMM_WORLD.rank

    class Formatter(logging.Formatter):
        def format(self, record):
            s1 = ('[ %09.2f ] % 3d: ' % (time.time() - t0, rank))
            return s1 + logging.Formatter.format(self, record)

    fmt = Formatter(fmt='%(asctime)s %(name)-15s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M ')

    global _logging_handler
    if _logging_handler is None:
        _logging_handler = logging.StreamHandler()
        logger.addHandler(_logging_handler)

    _logging_handler.setFormatter(fmt)
    logger.setLevel(levels[log_level])
