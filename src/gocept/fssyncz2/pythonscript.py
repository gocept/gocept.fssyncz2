import zope.fssync.synchronizer


class PythonScriptSynchronizer(zope.fssync.synchronizer.FileSynchronizer):

    def dump(self, writeable):
        writeable.write(self.context.read())

    def extras(self):
        return zope.fssync.synchronizer.Extras(title=self.context.title)
