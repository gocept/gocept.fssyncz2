import zope.fssync.synchronizer


class FolderSynchronizer(zope.fssync.synchronizer.DirectorySynchronizer):
    """Adapter to provide an fssync serialization of folders
    """

    def iteritems(self):
        """Compute a folder listing.

        A folder listing is a list of the items in the folder.  It is
        a combination of the folder contents and the site-manager, if
        a folder is a site.

        The adapter will take any mapping:

        >>> adapter = FolderSynchronizer({'x': 1, 'y': 2})
        >>> len(list(adapter.iteritems()))
        2

        """
        print self.context
        for key, value in self.context.objectItems():
            yield (key or '__empty__', value)

    def __setitem__(self, key, value):
        """Sets a folder item.

        >>> from zope.app.folder import Folder
        >>> folder = Folder()
        >>> adapter = FolderSynchronizer(folder)
        >>> adapter[u'test'] = 42
        >>> folder[u'test']
        42

        Since non-unicode names must be 7bit-ascii we try
        to convert them to unicode first:

        >>> adapter['t\xc3\xa4st'] = 43
        >>> adapter[u't\xe4st']
        43

        """
        if not isinstance(key, unicode):
            key = unicode(key, encoding='utf-8')
        if key == '__empty__':
            key = ''
        self.context._setOb(key, value)
