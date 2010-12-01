import OFS.Folder
import copy_reg
import zope.fssync.synchronizer


class FolderSynchronizer(zope.fssync.synchronizer.DirectorySynchronizer,
                         zope.fssync.synchronizer.DefaultSynchronizer):
    """Adapter to provide an fssync serialization of folders
    """

    def iteritems(self):
        """Compute a folder listing.

        A folder listing is a list of the items in the folder.  It is
        a combination of the folder contents and the site-manager, if
        a folder is a site.

        The adapter will take any mapping:

        >>> import OFS.Folder
        >>> import OFS.SimpleItem
        >>> folder = OFS.Folder.Folder()
        >>> _ = folder._setObject('x', OFS.SimpleItem.SimpleItem())
        >>> _ = folder._setObject('y', OFS.SimpleItem.SimpleItem())
        >>> adapter = FolderSynchronizer(folder)
        >>> len(list(adapter.iteritems()))
        2

        """
        for key, value in self.context.objectItems():
            yield (key or '__empty__', value)

    def __setitem__(self, key, value):
        """Sets a folder item.

        >>> import OFS.Folder
        >>> import OFS.SimpleItem
        >>> folder = OFS.Folder.Folder()
        >>> adapter = FolderSynchronizer(folder)
        >>> adapter[u'test'] = OFS.SimpleItem.SimpleItem()
        >>> folder[u'test']
        <SimpleItem at />

        """
        if not isinstance(key, unicode):
            key = unicode(key, encoding='utf-8')
        if key == '__empty__':
            key = ''
        self.context._setOb(key, value)

    def extras(self):
        extra = self.context.__dict__.copy()
        extra.pop('_objects', None)
        for key in self.context.objectIds():
            del extra[key]
        return zope.fssync.synchronizer.Extras(extra=extra)


def reduce(self):
    rv = super(type(self), self).__reduce__()
    if len(rv) >= 3 and rv[2] is not None:
        state = rv[2]
        for key in self.objectIds():
            del state[key]
    return rv


copy_reg.dispatch_table[OFS.Folder.Folder] = reduce
