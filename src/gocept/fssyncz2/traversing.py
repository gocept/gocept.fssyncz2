import zope.component
import zope.interface
import zope.traversing.interfaces

import OFS.interfaces


class OFSPhysicallyLocatable(object):

    zope.component.adapts(OFS.interfaces.IItem)
    zope.interface.implements(zope.traversing.interfaces.IPhysicallyLocatable)

    def __init__(self, context):
        self.context = context

    def getRoot(self):
        return self.context.getPhysicalRoot()

    def getPath(self):
        return self.context.getPhysicalPath()

    def getName(self):
        return self.context.getId()

    def getNearestSite(self):
        raise NotImplementedError
