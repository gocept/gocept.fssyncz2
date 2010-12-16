import Lifetime
import StringIO
import Testing.ZopeTestCase
import Testing.ZopeTestCase.layer
import random
import re
import time
import zope.fssync.snarf


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


def grep(pattern, lines):
    if not hasattr(lines, 'read'):
        lines = StringIO.StringIO(lines)
    pattern = re.compile(pattern)
    return ''.join(filter(pattern.search, lines))


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
        self.startZServer()

    @property
    def host(self):
        return Testing.ZopeTestCase.utils._Z2HOST

    @property
    def port(self):
        return Testing.ZopeTestCase.utils._Z2PORT

    def startZServer(self):
        if self.host is not None:
            return
        host = '127.0.0.1'
        port = random.choice(range(55000, 55500))
        from Testing.ZopeTestCase.threadutils import setNumberOfThreads
        setNumberOfThreads(5)
        from Testing.ZopeTestCase.threadutils import QuietThread, zserverRunner
        t = QuietThread(target=zserverRunner, args=(host, port, None))
        t.setDaemon(1)
        t.start()
        time.sleep(0.1)  # Sandor Palfy

        Testing.ZopeTestCase.utils._Z2HOST = host
        Testing.ZopeTestCase.utils._Z2PORT = port

    def tearDown(self):
        Lifetime.shutdown(0, fast=1)


server_layer = Zope2ServerLayer()
