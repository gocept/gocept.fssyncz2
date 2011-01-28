from zope.i18nmessageid import ZopeMessageFactory as _
import Missing
import cgi
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
import zope.xmlpickle.ppml
import gocept.fssyncz2.pickle_
import zope.traversing.interfaces
import Zope2


original_save = pickle.Pickler.save

def save(self, obj):
    if obj is Missing.Value:
        obj = None
    return original_save(self, obj)

pickle.Pickler.save = save

original_SyncTask__init__ = zope.fssync.task.SyncTask.__init__

def SyncTask__init__(self, *args, **kw):
    """Clear the guards oid cache and path."""
    gocept.fssyncz2.pickle_.seen.clear()
    gocept.fssyncz2.pickle_.path[:] = []
    original_SyncTask__init__(self, *args, **kw)

zope.fssync.task.SyncTask.__init__ = SyncTask__init__

def convert_string(self, string):
    """Convert a string to a form that can be included in XML text"""
    encoding = ''
    if zope.xmlpickle.ppml._binary_char(string):
        encoding = 'string_escape'
        string = string.encode(encoding)
    _, string = zope.xmlpickle.ppml._convert_sub(string)
    return encoding, string

zope.xmlpickle.ppml.String.convert = convert_string


def convert_unicode(self, string):
    _, string = zope.xmlpickle.ppml._convert_sub(
        string.encode('unicode_escape'))
    return 'unicode_escape', string

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
        super(CheckinCommitBase, self).createObject(container, name, *args, **kwargs)
        return container[name]


class Checkin(CheckinCommitBase, zope.fssync.task.Checkin):

    def perform(self, container, name, fspath):
        if container.hasObject(name):
            container.manage_delObjects([name])
        zope.fssync.task.Checkin.perform(self, container, name, fspath)


class Commit(CheckinCommitBase, zope.fssync.task.Commit):
    pass


class SnarfCheckinCommitBase(object):
    """Monkey Patch: Zope2 request behaviour."""

    def check_content_type(self):
        if not self.request.get_header("Content-Type") == "application/x-snarf":
            raise ValueError(_("Content-Type is not application/x-snarf"))

    def parse_args(self):
        qs = self.request.environ.get("QUERY_STRING")
        if qs:
            self.args = cgi.parse_qs(qs)
        else:
            self.args = {}


class SnarfCheckin(SnarfCheckinCommitBase, zope.app.fssync.browser.SnarfCheckin):
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
