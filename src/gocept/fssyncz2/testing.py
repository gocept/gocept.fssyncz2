# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import Lifetime
import StringIO
import Testing.ZopeTestCase
import Testing.ZopeTestCase.utils
import gocept.fssyncz2
import plone.testing
import plone.testing.z2
import plone.testing.zca
import re
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


def grep(pattern, lines, sort=False):
    if not hasattr(lines, 'read'):
        lines = StringIO.StringIO(lines)
    pattern = re.compile(pattern)
    lines = filter(pattern.search, lines)
    if sort:
        lines = sorted(lines)
    return ''.join(lines)


class _ZCMLSandbox(plone.testing.zca.ZCMLSandbox):
    """Layer which loads ZCML and resets TALES expressions on tear down.

    CAUTION: Not to be used directly, use ZCMLLayer, see above.

    """
    defaultBases = [plone.testing.z2.STARTUP]


class Zope2FunctionalLayer(_ZCMLSandbox,):

    __name__ = 'functional_layer'
    PRODUCTS = ['Products.Five',
                'Products.ZReST',
                'Products.PythonScripts',
                'Products.CookieUserFolder']

    def setUp(self):
        super(Zope2FunctionalLayer, self).setUp()
        with plone.testing.z2.zopeApp(self['zodbDB']) as app:
            for product in self.PRODUCTS:
                plone.testing.z2.installProduct(app, product)


functional_layer = Zope2FunctionalLayer(
    None, 'gocept.fssyncz2:ZCML', __name__, 'ftesting.zcml',
    gocept.fssyncz2)


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


server_layer = Zope2ServerLayer(
    None, 'gocept.fssyncz2:ZCML', __name__, 'ftesting.zcml',
    gocept.fssyncz2)


# gocept.zodb.dbiterator
# This is copied from Steppkes. If it makes eggified to the pypi some day,
# delete this code and use the egg instead

import logging  # NOQA
from zope.interface import Interface, implements  # NOQA
from ZODB.POSException import POSKeyError  # NOQA
from ZODB.utils import oid_repr  # NOQA


class IDatabaseIterator(Interface):

    def __iter__():
        """Iterates over all objects in database."""


class IOIDLoader(Interface):
    """Provide the capability to retrieve all oids from a storage."""

    def getOIDs():
        """Return an iterable of all oids."""


class FileStorageOIDs(object):
    """Provide the capability to retrieve all oids from a file storage."""
    implements(IOIDLoader)

    def __init__(self, storage):
        self.storage = storage

    def getOIDs(self):
        """Return an iterable of all oids."""
        return self.storage.changes._data.keys()


class DatabaseIterator(object):
    """Iterator usable for a FileStorage."""
    implements(IDatabaseIterator)

    def __init__(self, connection):
        self.connection = connection

    def __iter__(self):
        """Iterates over all objects in database."""
        storage = self.connection._storage
        oid_loader = IOIDLoader(storage)
        for oid in oid_loader.getOIDs():
            try:
                object = self.connection.get(oid)
            except POSKeyError:
                # XXX warg. For some reason the oids we get back might refer to
                # non-existing objects, although the database seems consistent.
                log = logging.getLogger("gocept.zodb")
                log.warn("Found POSKeyError while iterating over database. "
                         "OID: %s" % oid_repr(oid))
                continue
            yield object
