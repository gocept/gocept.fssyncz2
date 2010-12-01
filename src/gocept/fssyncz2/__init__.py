import Missing
import cgi
import pickle
import zope.app.fssync.browser
import zope.app.fssync.syncer
import zope.component
import zope.fssync.interfaces
import zope.fssync.repository
import zope.fssync.task
import zope.interface
import zope.security.proxy
import zope.xmlpickle.ppml


OriginalPickler = pickle.Pickler


class MissingSafePickler(OriginalPickler):

    def save(self, obj):
        if obj is Missing.Value:
            obj = None
        return OriginalPickler.save(self, obj)

pickle.Pickler = MissingSafePickler


def convert_string(self, string):
    """Convert a string to a form that can be included in XML text"""
    if zope.xmlpickle.ppml._binary_char(string):
        encoding = 'string_escape'
    else:
        encoding = ''
    _, string = zope.xmlpickle.ppml._convert_sub(
        string.encode('string_escape'))
    return encoding, string

zope.xmlpickle.ppml.String.convert = convert_string


def convert_unicode(self, string):
    if zope.xmlpickle.ppml._invalid_xml_char(string):
        encoding = 'unicode_escape'
    else:
        encoding = ''
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
        string = string.encode('ascii').decode('unicode_escape')
    elif encoding:
        raise ValueError('bad encoding', encoding)
    return string

zope.xmlpickle.ppml.unconvert_unicode = unconvert_unicode


class Unicode(zope.xmlpickle.ppml.Unicode):

    def convert(self, string):
        if zope.xmlpickle.ppml._invalid_xml_char(string):
            string = string.encode('utf-8')
            return 'utf-8', string
        return zope.xmlpickle.ppml._convert_sub(string.encode('utf-8'))


class SnarfFile(zope.app.fssync.browser.SnarfFile):

    def show(self):
        return super(SnarfFile, self).show().read()


class SnarfCommit(zope.app.fssync.browser.SnarfCheckin):

    def check_content_type(self):
        if not self.request.get_header("Content-Type") == "application/x-snarf":
            raise ValueError(_("Content-Type is not application/x-snarf"))

    def parse_args(self):
        # The query string in the URL didn't get parsed, because we're
        # getting a POST request with an unrecognized content-type
        qs = self.request.environ.get("QUERY_STRING")
        if qs:
            self.args = cgi.parse_qs(qs)
        else:
            self.args = {}


class SnarfCheckin(SnarfCommit):

    def run_submission(self):
        stream = self.request.stdin
        snarf = zope.fssync.repository.SnarfRepository(stream)
        checkin = zope.fssync.task.Checkin(
            zope.app.fssync.syncer.getSynchronizer, snarf)
        checkin.perform(self.container, self.name, self.fspath)
        return ""


class InsecureCheckout(zope.fssync.task.Checkout):

    def dump(self, synchronizer, path):
        if synchronizer is None:
            return

        def dump_directory(path):
            valid = True
            items = [(x, y, zope.security.proxy.removeSecurityProxy(s))
                     for x, y, s in self.serializableItems(synchronizer.iteritems(), path)]
            self.dumpSpecials(path, items)
            for name, key, s in items:   # recurse down the tree
                self.dump(s, self.repository.join(path, name))

        def dump_file(path):
            fp = self.repository.writeable(path)
            zope.security.proxy.removeSecurityProxy(synchronizer).dump(fp)
            fp.close()

        if zope.fssync.interfaces.IDirectorySynchronizer.providedBy(synchronizer):
            dump_directory(path)
        elif zope.fssync.interfaces.IFileSynchronizer.providedBy(synchronizer):
            dump_file(path)
        else:
            raise zope.fssync.task.SynchronizationError("invalid synchronizer")


zope.fssync.task.Checkout = InsecureCheckout


@zope.component.adapter(zope.interface.Interface)
@zope.interface.implementer(zope.fssync.interfaces.IEntryId)
def EntryId(obj):
    try:
        path = obj.absolute_url_path()
        return path.encode('utf-8')
    except (TypeError, KeyError, AttributeError):
        # this case can be triggered for persistent objects that don't
        # have a name in the content space (annotations, extras)
        return None
