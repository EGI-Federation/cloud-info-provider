class BaseProvider(object):
    def __init__(self, opts):
        pass

    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""
