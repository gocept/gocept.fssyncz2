# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import OFS.interfaces
import zope.component
import zope.interface
import zope.traversing.interfaces


class OFSPhysicallyLocatable(object):

    zope.component.adapts(OFS.interfaces.IItem)
    zope.interface.implements(zope.traversing.interfaces.IPhysicallyLocatable)

    def __init__(self, context):
        self.context = context

    def getParent(self):
        return self.context.aq_inner.aq_parent

    def getRoot(self):
        return self.context.getPhysicalRoot()

    def getPath(self):
        return self.context.getPhysicalPath()

    def getName(self):
        return self.context.getId()

    def getNearestSite(self):
        raise NotImplementedError
