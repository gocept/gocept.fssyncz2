# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.fssync.interfaces
import zope.fssync.pickle
import zope.xmlpickle.xmlpickle


seen = {}
path = []


class DuplicateOIdPreventingPickler(
    zope.xmlpickle.xmlpickle._PicklerThatSortsDictItems):

    def save(self, obj):
        path.append(repr(obj))
        try:
            oid = obj._p_oid
        except:
            pass
        else:
            if isinstance(oid, str):
                if oid in seen:
                    raise RuntimeError(
                        'Duplicate OId %r: %s, %s' % (oid, seen[oid], path))
                seen[oid] = path
        zope.xmlpickle.xmlpickle._PicklerThatSortsDictItems.save(self, obj)
        path.pop()


class UnwrappedPickler(zope.fssync.pickle.XMLPickler):

    def __init__(self, context):
        super(UnwrappedPickler, self).__init__(context)
        try:
            self.context = self.context.aq_base
        except AttributeError:
            pass


def dump(self, writeable):
    # MonkeyPatch: Inject our DuplicateOIdPreventingPickler
    pickler = DuplicateOIdPreventingPickler(writeable, 0)
    generator = zope.fssync.interfaces.IPersistentIdGenerator(self, None)
    if generator is not None:
        pickler.persistent_id = generator.id
    pickler.dump(self.context)

zope.fssync.pickle.StandardPickler.dump = dump
