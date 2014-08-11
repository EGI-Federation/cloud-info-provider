import logging
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class BaseException(Exception):
    msg_fmt = 'An unknown exception occurred.'

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                logger.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    logger.error('%s: %s' % (name, value))
                raise exc_info[0], exc_info[1], exc_info[2]

        super(BaseException, self).__init__(message)


class OpenStackProviderException(BaseException):
    pass


class StaticProviderException(BaseException):
    pass
