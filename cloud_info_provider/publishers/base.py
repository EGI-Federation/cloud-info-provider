class BasePublisher(object):
    def __init__(self, opts):
        self.opts = opts

    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""
        pass

    def publish(self, output):
        raise NotImplementedError
