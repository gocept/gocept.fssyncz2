import Lifetime
import Missing
import Testing.ZopeTestCase
import Testing.ZopeTestCase.layer
import pickle
import random
import time
import unittest
import urllib2
import zope.testbrowser.browser


class Zope2ObjectsTest(unittest.TestCase):
    """Make sure that we can handle Zope2 objects.

    """

    def test_missing_value(self):
        try:
            pickle.dumps({'foo': Missing.Value})
        except TypeError, e:
            self.fail(e)
        self.assert_("(dp0\nS'foo'\np1\nNs.",
                     repr(pickle.dumps({'foo': Missing.Value})))


class Zope2FunctionalLayer(object):
    """Make sure checkout doesn't fail with Zope2.

    """

    __bases__ = (Testing.ZopeTestCase.layer.ZopeLiteLayer,)
    __name__ = 'layer'

    def setUp(self):
        Testing.ZopeTestCase.installProduct('Five')
        Testing.ZopeTestCase.layer.ZopeLiteLayer.setUp()
        Testing.ZopeTestCase.installPackage('gocept.fssyncz2')
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


functional_layer = Zope2FunctionalLayer()


class CheckoutTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure checkout doesn't fail with Zope2.

    """

    layer = functional_layer

    def setUp(self):
        Testing.ZopeTestCase.ZopeTestCase.setUp(self)
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('file', 'foo')
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_remove_security_proxies(self):
        browser = zope.testbrowser.browser.Browser()
        browser.addHeader('Authorization',
                          'Basic '+'manager:asdf'.encode('base64'))
        try:
            browser.open(
                'http://localhost:%s/folder/@@toFS.snarf' % self.layer.port)
        except urllib2.HTTPError, e:
            self.fail(e)


def test_suite():
    return unittest.TestSuite(
        (unittest.makeSuite(Zope2ObjectsTest),
         unittest.makeSuite(CheckoutTests)))
