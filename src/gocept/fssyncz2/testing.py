# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import Lifetime
import StringIO
import Testing.ZopeTestCase
import Testing.ZopeTestCase.layer
import re
import zope.fssync.snarf
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


class Zope2FunctionalLayer(object):

    __bases__ = (Testing.ZopeTestCase.layer.ZopeLiteLayer,)
    __name__ = 'functional_layer'

    def setUp(self):
        Testing.ZopeTestCase.installProduct('Five')
        Testing.ZopeTestCase.installProduct('ZReST')
        Testing.ZopeTestCase.installProduct('PythonScripts')
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


# gocept.zodb.dbiterator
# This is copied from Steppkes. If it makes eggified to the pypi some day,
# delete this code and use the egg instead

import logging
from zope.interface import Interface, implements
from ZODB.POSException import POSKeyError
from ZODB.utils import oid_repr


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
        return self.storage._index.keys()


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
