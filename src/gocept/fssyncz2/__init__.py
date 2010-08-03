import Missing
import pickle
import zope.app.fssync.browser
import zope.fssync.interfaces
import zope.fssync.task
import zope.security.proxy


OriginalPickler = pickle.Pickler


class MissingSafePickler(OriginalPickler):

    def save(self, obj):
        if obj is Missing.Value:
            obj = None
        return OriginalPickler.save(self, obj)

pickle.Pickler = MissingSafePickler


class SnarfFile(zope.app.fssync.browser.SnarfFile):

    def show(self):
        return super(SnarfFile, self).show().read()


class InsecureCheckout(zope.fssync.task.Checkout):

    def dump(self, synchronizer, path):
        if synchronizer is None:
            return
        if zope.fssync.interfaces.IDirectorySynchronizer.providedBy(synchronizer):
            items = [(x, y, zope.security.proxy.removeSecurityProxy(s))
                     for x, y, s in self.serializableItems(synchronizer.iteritems(), path)]
            self.dumpSpecials(path, items)
            for name, key, s in items:   # recurse down the tree
                self.dump(s, self.repository.join(path, name))
        elif zope.fssync.interfaces.IFileSynchronizer.providedBy(synchronizer):
            fp = self.repository.writeable(path)
            zope.security.proxy.removeSecurityProxy(synchronizer).dump(fp)
            fp.close()
        else:
            raise zope.fssync.task.SynchronizationError("invalid synchronizer")


zope.fssync.task.Checkout = InsecureCheckout
