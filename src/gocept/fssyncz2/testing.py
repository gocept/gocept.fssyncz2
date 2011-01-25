import Lifetime
import StringIO
import Testing.ZopeTestCase
import Testing.ZopeTestCase.layer
import random
import re
import time
import zope.fssync.snarf
import zope.fssync.tests.test_task
import zope.fssync.synchronizer
import Testing.ZopeTestCase.utils


class Lines(StringIO.StringIO):

    def __iter__(self):
        self.seek(0)
        return self

    def close(self):
        pass


class SnarfAsDict(zope.fssync.snarf.Unsnarfer, dict):

    def __init__(self, istr):
        super(SnarfAsDict, self).__init__(istr)

    def makedir(self, path):
        pass

    def createfile(self, path):
        f = self[path] = Lines()
        return f


def unsnarf(response, path):
    unsnarfed = SnarfAsDict(StringIO.StringIO(response.getBody()))
    unsnarfed.unsnarf('')
    return unsnarfed[path]


def grep(pattern, lines, sort=False):
    if not hasattr(lines, 'read'):
        lines = StringIO.StringIO(lines)
    pattern = re.compile(pattern)
    lines = filter(pattern.search, lines)
    if sort:
        lines = sorted(lines)
    return ''.join(lines)


class ExampleFile(zope.fssync.tests.test_task.ExampleFile):

    def _setId(self, key):
        self.id = key


class PretendContainer(zope.fssync.tests.test_task.PretendContainer):

    def _setObject(self, key, value, **kw):
        self[key] = value

    def _delObject(self, key, **kw):
        del self[key]

    def objectItems(self):
        return self.holding.iteritems()

    def objectIds(self):
        return self.holding.keys()


class FileSynchronizer(zope.fssync.synchronizer.FileSynchronizer):
    """A convenient base class for file serializers."""

    def dump(self, writeable):
        writeable.write(self.context.data)

    def load(self, readable):
        self.context.data = readable.read()



class Zope2FunctionalLayer(object):

    __bases__ = (Testing.ZopeTestCase.layer.ZopeLiteLayer,)
    __name__ = 'functional_layer'

    def setUp(self):
        Testing.ZopeTestCase.installProduct('Five')
        Testing.ZopeTestCase.layer.ZopeLiteLayer.setUp()


functional_layer = Zope2FunctionalLayer()


class Zope2ServerLayer(Zope2FunctionalLayer):

    __name__ = 'server_layer'

    def setUp(self):
        super(Zope2ServerLayer, self).setUp()
        # We need to access the Zope2 server from outside in order to see
        # effects related to security proxies.
        Testing.ZopeTestCase.utils.startZServer()

    @property
    def host(self):
        return Testing.ZopeTestCase.utils._Z2HOST

    @property
    def port(self):
        return Testing.ZopeTestCase.utils._Z2PORT

    def tearDown(self):
        Lifetime.shutdown(0, fast=1)


server_layer = Zope2ServerLayer()
