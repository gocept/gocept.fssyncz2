# Copyright (c) 2011-2012 gocept gmbh & co. kg
# See also LICENSE.txt

from zope.i18nmessageid import ZopeMessageFactory as _
import Missing
import cgi
import gocept.fssyncz2.folder
import gocept.fssyncz2.pickle_
import pickle
import zope.app.fssync.browser
import zope.app.fssync.syncer
import zope.component
import zope.fssync.interfaces
import zope.fssync.repository
import zope.fssync.synchronizer
import zope.fssync.task
import zope.interface
import zope.security.proxy
import zope.traversing.interfaces
import zope.xmlpickle.ppml


def save(self, obj):
    if obj is Missing.Value:
        obj = None
    return original_save(self, obj)

original_save = pickle.Pickler.save
pickle.Pickler.save = save


def SyncTask__init__(self, *args, **kw):
    """Clear the guards oid cache and path."""
    gocept.fssyncz2.pickle_.seen.clear()
    gocept.fssyncz2.pickle_.path[:] = []
    original_SyncTask__init__(self, *args, **kw)

original_SyncTask__init__ = zope.fssync.task.SyncTask.__init__
zope.fssync.task.SyncTask.__init__ = SyncTask__init__


def _convert_sub(string):
    # This is the converter almost straight from zope.xmlpickle.ppml but with
    # an added encoding for >. Maybe this change should be merged upstream, or
    # maybe we should give up on retaining \r and always use CDATA (though
    # splitting the string into several sections where it contains the
    # sequence ]]>, ]] going into one, > into the other).

    # We don't want to get returns "normalized away, so we quote them
    # This means we can't use cdata.
    rpos = string.find('\r')
    lpos = string.find('<')
    gpos = string.find('>')
    apos = string.find('&')

    if rpos >= 0 or lpos >= 0 or gpos >= 0 or apos >= 0:

        # Need to do something about special characters
        if rpos < 0 and string.find(']]>') < 0:
            # can use cdata
            string = "<![CDATA[%s]]>" % string
        else:
            if apos >= 0:
                string = string.replace("&", "&amp;")
            if lpos >= 0:
                string = string.replace("<", "&lt;")
            if gpos >= 0:
                string = string.replace(">", "&gt;")
            if rpos >= 0:
                string = string.replace("\r", "&#x0d;")

    return '', string


def convert_string(self, string):
    """Convert a string to a form that can be included in XML text"""
    encoding = ''
    if zope.xmlpickle.ppml._binary_char(string):
        encoding = 'string_escape'
        string = '\n'.join(s.encode(encoding) for s in string.split('\n'))
    _, string = _convert_sub(string)
    return encoding, string

zope.xmlpickle.ppml.String.convert = convert_string


def convert_unicode(self, string):
    encoding = 'unicode_escape'
    _, string = _convert_sub(
        '\n'.join(s.encode(encoding) for s in string.split('\n')))
    return encoding, string

zope.xmlpickle.ppml.Unicode.convert = convert_unicode


def unconvert_string(encoding, string):
    if encoding == 'string_escape':
        return string.decode('string_escape')
    elif encoding:
        raise ValueError('bad encoding', encoding)
    return string

zope.xmlpickle.ppml.unconvert_string = unconvert_string


def unconvert_unicode(encoding, string):
    if encoding == 'unicode_escape':
        string = string.encode(
            'ascii').decode('unicode_escape').encode('utf-8')
    elif encoding:
        raise ValueError('bad encoding', encoding)
    return string

zope.xmlpickle.ppml.unconvert_unicode = unconvert_unicode


def getSynchronizer(obj, raise_error=True):
    # Monkey Patch: Remove Zope3 security proxy wrapping
    dn = zope.fssync.synchronizer.dottedname(obj.__class__)

    factory = zope.component.queryUtility(
        zope.fssync.interfaces.ISynchronizerFactory, name=dn)
    if factory is None:
        factory = zope.component.queryUtility(
            zope.fssync.interfaces.ISynchronizerFactory)
    if factory is None:
        if raise_error:
            raise zope.fssync.synchronizer.MissingSynchronizer(dn)
        return None
    return factory(obj)

zope.app.fssync.syncer.getSynchronizer = getSynchronizer


class SnarfFile(zope.app.fssync.browser.SnarfFile):

    def show(self):
        # XXX decorate
        return super(SnarfFile, self).show().read()


class CheckinCommitBase(object):

    def createObject(self, container, name, *args, **kwargs):
        # Monkey Patch: Acquisition wrap
        super(CheckinCommitBase, self).createObject(
            container, name, *args, **kwargs)
        return container[name]


class Checkin(CheckinCommitBase, zope.fssync.task.Checkin):

    def perform(self, container, name, fspath):
        temp_name = name + '__gocept_fssyncz2_load_in_progress_'
        if container.hasObject(name):
            container.manage_renameObject(name, temp_name)
        super(Checkin, self).perform(container, name, fspath)
        if container.hasObject(temp_name):
            self.restore_ignored_objects(
                container[temp_name], container[name])
            container.manage_delObjects([temp_name])

    def restore_ignored_objects(self, old, new):
        synchronizer = self.getSynchronizer(new)
        if not isinstance(
            synchronizer, gocept.fssyncz2.folder.FolderSynchronizer):
            return
        for name, obj in new.objectItems():
            try:
                old_obj = old[name]
            except KeyError:
                continue
            self.restore_ignored_objects(old_obj, obj)
        new.manage_pasteObjects(
            old.manage_cutObjects(synchronizer.ignored_items))


class Commit(CheckinCommitBase, zope.fssync.task.Commit):
    pass


class SnarfCheckinCommitBase(object):
    """Monkey Patch: Zope2 request behaviour."""

    def check_content_type(self):
        if self.request.get_header("Content-Type") != "application/x-snarf":
            raise ValueError(_("Content-Type is not application/x-snarf"))

    def parse_args(self):
        qs = self.request.environ.get("QUERY_STRING")
        if qs:
            self.args = cgi.parse_qs(qs)
        else:
            self.args = {}


class SnarfCheckin(
    SnarfCheckinCommitBase, zope.app.fssync.browser.SnarfCheckin):
    """Monkey Patch: Zope2 request behaviour."""

    def run_submission(self):
        stream = self.request.stdin
        snarf = zope.fssync.repository.SnarfRepository(stream)
        checkin = Checkin(getSynchronizer, snarf)
        checkin.perform(self.container, self.name, self.fspath)
        return "All done."


class SnarfCommit(SnarfCheckinCommitBase, zope.app.fssync.browser.SnarfCommit):

    def set_arguments(self):
        # Monkey Patch: Inject IPhysicallyLocatable (thx zope.traversing.api)
        context = zope.traversing.interfaces.IPhysicallyLocatable(self.context)
        self.name = context.getName()
        self.container = context.getParent()
        if self.container is None and self.name == "":
            self.container = context.getRoot()
            self.fspath = 'root'
        else:
            self.fspath = self.name

    def get_checker(self, raise_on_conflicts=False):
        # Monkey Patch: Zope2 request
        stream = self.request.stdin
        snarf = zope.fssync.repository.SnarfRepository(stream)
        return zope.fssync.task.Check(getSynchronizer, snarf,
                        raise_on_conflicts=raise_on_conflicts)

    def run_submission(self):
        # XXX decorate
        self.call_checker()
        if self.errors:
            return self.send_errors()
        else:
            stream = self.request.stdin
            snarf = zope.fssync.repository.SnarfRepository(stream)
            c = Commit(getSynchronizer, snarf)
            c.perform(self.container, self.name, self.fspath)
            return self.send_archive().read()


@zope.component.adapter(zope.interface.Interface)
@zope.interface.implementer(zope.fssync.interfaces.IEntryId)
def EntryId(obj):
    # Copied from: zope.fssync.task.py
    # Monkey Patch: zope.traversing (again...)
    try:
        path = '/'.join(
            zope.traversing.interfaces.IPhysicallyLocatable(obj).getPath())
        return path.encode('utf-8')
    except (TypeError, KeyError, AttributeError):
        # this case can be triggered for persistent objects that don't
        # have a name in the content space (annotations, extras)
        return None
