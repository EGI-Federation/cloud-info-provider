import abc


class BaseFormatter:
    """Base class for the formatters."""

    __metaclass__ = abc.ABCMeta

    def format(self, opts, glue):
        raise NotImplementedError
