import AccessControl.User
import OFS.Folder
import copy_reg
import zope.fssync.synchronizer
import persistent


class FolderSynchronizer(zope.fssync.synchronizer.DirectorySynchronizer):
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

        >>> import Zope2
        >>> app = Zope2.app()
        >>> app.manage_addFolder('folder')
        >>> adapter = FolderSynchronizer(app['folder'])
        >>> import OFS.SimpleItem
        >>> adapter['test'] = OFS.SimpleItem.SimpleItem()
        >>> app['folder']['test']
        <SimpleItem at /folder/test>

        """
        if key == '__empty__':
            key = ''
        value._setId(key)
        self.context._setObject(
            key, value, set_owner=False, suppress_events=True)
        if isinstance(value, AccessControl.User.BasicUserFolder):
            self.context.__allow_groups__ = value

    def __delitem__(self, key):
        """Deletes a folder item.

        >>> import Zope2
        >>> app = Zope2.app()
        >>> app.manage_addFolder('folder')
        >>> adapter = FolderSynchronizer(app['folder'])
        >>> import OFS.SimpleItem
        >>> adapter['test'] = OFS.SimpleItem.SimpleItem()
        >>> app['folder']['test']
        <SimpleItem at /folder/test>
        >>> del adapter['test']
        >>> app['folder']['test']
        Traceback (most recent call last):
        KeyError: 'test'

        """
        if key == '__empty__':
            key = ''
        self.context._delObject(key, suppress_events=True)

    def extras(self):
        extra = self.context.__dict__.copy()
        extra.pop('_objects', None)
	extra.pop('__allow_groups__', None)
        extra.pop('id', None)
        for key in self.context.objectIds():
            del extra[key]
	for k, v in extra.items():
	    if isinstance(v, persistent.Persistent) or isinstance(k, persistent.Persistent):
                raise RuntimeError('Persistent object in Extras found: %s: %s' % (k,v))
        return zope.fssync.synchronizer.Extras(attributes=extra)

    def setextras(self, extras):
        self.context.__dict__.update(extras['attributes'])


def reduce(self):
    rv = super(type(self), self).__reduce__()
    if len(rv) >= 3 and rv[2] is not None:
        state = rv[2]
        for key in self.objectIds():
            del state[key]
    return rv


copy_reg.dispatch_table[OFS.Folder.Folder] = reduce
