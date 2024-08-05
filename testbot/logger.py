import logging

logging.basicConfig()
logger = logging.getLogger("agent")


def init_logger(_logger, filepath, mode="a"):
    _logger.setLevel(logging.DEBUG)

    fmt = '%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s'
    formatter = logging.Formatter(fmt)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    _logger.addHandler(console)

    fout = logging.FileHandler(filepath, mode=mode)
    fout.setLevel(logging.DEBUG)
    fout.setFormatter(formatter)
    _logger.addHandler(fout)

    # Do not propagate message to its ancestors.
    _logger.propagate = False

    _logger.info('logger inited')


init_logger(logger, "agent.log", "w")
