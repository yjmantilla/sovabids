"""Module dealing with logging related functionality and settings"""

import os
import logging
import sys

def _excepthook(*args):
    """Catch Exceptions to logger.
    
    Notes
    -----
    See https://code.activestate.com/recipes/577074-logging-asserts/
    """
    logging.getLogger().error('Uncaught exception:', exc_info=args)

sys.excepthook = _excepthook # See _excepthook documentation


def setup_logging(log_file=None, debug=False):
    """Setup the logging

    Parameters
    ----------
    log_file: str
        Name of the logfile
    debug: bool
        Set log level to DEBUG if debug==True

    Returns
    -------
    logging.logger:
        The logger. None if no log_file provided.

    
    Notes
    -----
    This function is a copy of the one found in bidscoin.
    https://github.com/Donders-Institute/bidscoin/blob/748ea2ba537b06d8eee54ac7217b909bdf91a812/bidscoin/bidscoin.py#L41-L83
    """

    # Get the root logger
    logger = logging.getLogger()

    # Set the format and logging level
    if debug:
        fmt = '%(asctime)s - %(name)s - %(levelname)s | %(message)s'
        logger.setLevel(logging.DEBUG)
    else:
        fmt = '%(asctime)s - %(levelname)s | %(message)s'
        logger.setLevel(logging.INFO)
    datefmt   = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # Set & add the streamhandler and add some color to those boring terminal logs! :-)
    #coloredlogs.install(level=logger.level, fmt=fmt, datefmt=datefmt)

    if not log_file:
        return logger

    # Set & add the log filehandler
    logdir,_ = os.path.split(log_file)
    os.makedirs(logdir,exist_ok=True) # Create the log dir if it does not exist
    loghandler = logging.FileHandler(log_file)
    loghandler.setLevel(logging.DEBUG)
    loghandler.setFormatter(formatter)
    loghandler.set_name('loghandler')
    logger.addHandler(loghandler)

    # Set & add the error / warnings handler
    error_file = os.path.join(logdir,log_file+'.errors')            # Derive the name of the error logfile from the normal log_file
    errorhandler = logging.FileHandler(error_file, mode='w')
    errorhandler.setLevel(logging.WARNING)
    errorhandler.setFormatter(formatter)
    errorhandler.set_name('errorhandler')
    logger.addHandler(errorhandler)
    return logger
