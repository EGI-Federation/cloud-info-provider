import logging

logger = logging.getLogger(__name__)


class CloudInfoException(Exception):
    msg_fmt = "An unknown exception occurred."

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                logger.exception("Exception in string format operation")
                for name, value in kwargs.items():
                    logger.error("%s: %s" % (name, value))
                raise

        super().__init__(message)


class OpenStackProviderException(CloudInfoException):
    pass
