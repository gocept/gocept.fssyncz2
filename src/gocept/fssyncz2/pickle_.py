import zope.fssync.pickle


class UnwrappedPickler(zope.fssync.pickle.XMLPickler):

    def __init__(self, context):
        super(UnwrappedPickler, self).__init__(context)
        try:
            self.context = self.context.aq_base
        except AttributeError:
            pass
