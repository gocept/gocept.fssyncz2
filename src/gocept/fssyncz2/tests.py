from gocept.fssyncz2.testing import unsnarf, grep
import Missing
import OFS.SimpleItem
import StringIO
import Testing.ZopeTestCase
import doctest
import gocept.fssyncz2.testing
import gocept.fssyncz2.traversing
import httplib
import pickle
import random
import unittest
import urllib2
import zope.testbrowser.browser
import zope.fssync.tests.test_task
import zope.fssync.synchronizer
import zope.app.fssync.main
import os.path
import lxml
import pyquery
import transaction


class Zope2ObjectsTest(unittest.TestCase):
    """Make sure that we can handle Zope2 objects.

    """

    def test_missing_value(self):
        try:
            pickle.dumps({'foo': Missing.Value})
        except TypeError, e:
            self.fail(e)
        self.assert_("(dp0\nS'foo'\np1\nNs.",
                     repr(pickle.dumps({'foo': Missing.Value})))


class ViewTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure checkout doesn't fail with Zope2.

    """

    layer = gocept.fssyncz2.testing.server_layer

    def setUp(self):
        Testing.ZopeTestCase.ZopeTestCase.setUp(self)
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('file', 'foo')
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_checkout_response_should_be_OK_and_a_snarf_archive(self):
        browser = zope.testbrowser.browser.Browser()
        browser.addHeader('Authorization',
                          'Basic '+'manager:asdf'.encode('base64'))
        try:
            browser.open(
                'http://localhost:%s/folder/@@toFS.snarf' % self.layer.port)
        except urllib2.HTTPError, e:
            self.fail(e)
        self.assertEquals("""\
00000167 @@Zope/Extra/folder/@@Zope/Entries.xml
00000186 folder/@@Zope/Entries.xml
00000223 @@Zope/Entries.xml
00000605 @@Zope/Extra/folder/attributes
00001210 folder/file
""", grep('^[0-9]{8}', browser.contents, sort=True))

    def test_checkin_response_should_be_OK_objects_created_and_wrapped(self):
        snarf = """\
0 @@Zope/
0 @@Zope/Extra/
0 @@Zope/Extra/folder/
0 @@Zope/Extra/folder/@@Zope/
140 @@Zope/Extra/folder/@@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
  <entry name="attributes" keytype="__builtin__.str" type="__builtin__.dict" />
</entries>
139 @@Zope/Extra/folder/attributes
<?xml version="1.0" encoding="utf-8" ?>
<pickle>
  <dictionary>
    <item key="title"> <string></string> </item>
  </dictionary>
</pickle>
187 @@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
  <entry name="folder" keytype="__builtin__.str"
         type="OFS.Folder.Folder" factory="OFS.Folder.Folder" id="/folder" />
</entries>
0 folder/
0 folder/@@Zope/
159 folder/@@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
  <entry name="file" keytype="__builtin__.str"
         type="OFS.Image.File" id="/folder/file" />
</entries>
807 folder/file
<?xml version="1.0" encoding="utf-8" ?>
<pickle>
  <initialized_object>
    <klass>
      <global name="__newobj__" module="copy_reg"/>
    </klass>
    <arguments>
      <tuple>
        <global name="File" module="OFS.Image"/>
      </tuple>
    </arguments>
    <state>
      <dictionary>
        <item key="_EtagSupport__etag"> <string>ts92221379.71</string> </item>
        <item key="__name__"> <string>file</string> </item>
        <item key="content_type"> <string>application/octet-stream</string> </item>
        <item key="data"> <string>foo</string> </item>
        <item key="precondition"> <string id="o0"></string> </item>
        <item key="size"> <int>3</int> </item>
        <item key="title"> <reference id="o0"/> </item>
      </dictionary>
    </state>
  </initialized_object>
</pickle>
"""
        self.assertFalse('folder2' in self.app.objectIds())

        conn = httplib.HTTPConnection('localhost:%s' % self.layer.port)
        conn.putrequest('POST',
                        '/@@checkin.snarf?note=test&name=folder2&src=folder')
        conn.putheader('Content-Type', 'application/x-snarf')
        conn.putheader('Content-Length', str(len(snarf)))
        conn.putheader('Authorization',
                       'Basic '+'manager:asdf'.encode('base64'))
        conn.putheader('Host', 'localhost:%s' % self.layer.port)
        conn.putheader('Connection', 'close')
        conn.endheaders()
        conn.send(snarf)

        response = conn.getresponse()
        self.assertEqual(204, response.status)
        self.assertEqual(
            '<File at /folder2/file>', repr(self.app['folder2']['file']))


class ReferencesTest(Testing.ZopeTestCase.FunctionalTestCase):

    layer = gocept.fssyncz2.testing.functional_layer

    def setUp(self):
        super(ReferencesTest, self).setUp()
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])
    def test_multiple_references_to_one_object_abort_checkout(self):
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('foo', '')
        self.app['folder'].manage_addFile('bar', '')
        response = self.publish(
            '/folder/@@toFS.snarf', basic='manager:asdf')
        body = response.getBody()
        self.assertTrue('foo' in body)
        self.assertTrue('bar' in body)
        self.app['folder']['foo'].my_ref = self.app['folder']['bar']
        response = self.publish(
            '/folder/@@toFS.snarf', basic='manager:asdf')
        self.assertTrue("""doppelt: [\'<File at foo>\', "{\'precondition\': \'\', \'my_ref\': <File at bar>,""" in response.getBody())


class FolderTest(Testing.ZopeTestCase.FunctionalTestCase):

    layer = gocept.fssyncz2.testing.functional_layer

    def setUp(self):
        super(FolderTest, self).setUp()
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_folder_is_pickled_with_entries_and_attributes(self):
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('foo', 'bar')
        self.app['folder'].a = 'asdf'
        self.app['folder'].b = 'bsdf'
        response = self.publish(
            '/folder/@@toFS.snarf', basic='manager:asdf')
        self.assertEquals("""\
  <entry name="foo"
""", grep('<entry', unsnarf(response, 'folder/@@Zope/Entries.xml')))
        self.assertTrue("""\
        <dictionary>
          <item key="__ac_local_roles__">
              <dictionary>
                <item key="test_user_1_">
                    <list>
                      <string>Owner</string>
                    </list>
                </item>
              </dictionary>
          </item>
          <item key="_owner">
              <tuple>
                <list>
                  <string>test_folder_1_</string>
                  <string>acl_users</string>
                </list>
                <string>test_user_1_</string>
              </tuple>
          </item>
          <item>
            <key> <string>a</string> </key>
            <value> <string>asdf</string> </value>
          </item>
          <item>
            <key> <string>b</string> </key>
            <value> <string>bsdf</string> </value>
          </item>
          <item key="id">
              <string>folder</string>
          </item>
          <item key="title">
              <string></string>
          </item>
        </dictionary>
""", unsnarf(response, '@@Zope/Extra/folder/attributes'))

    def test_folder_attributes_are_unpickled(self):
        snarf = """\
0 @@Zope/
0 @@Zope/Extra/
0 @@Zope/Extra/folder/
0 @@Zope/Extra/folder/@@Zope/
140 @@Zope/Extra/folder/@@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
  <entry name="attributes" keytype="__builtin__.str" type="__builtin__.dict" />
</entries>
289 @@Zope/Extra/folder/attributes
<?xml version="1.0" encoding="utf-8" ?>
<pickle>
  <dictionary>
    <item key="title"> <string></string> </item>
    <item key="foo"> <string>FOO</string> </item>
    <item key="bar"> <string>BAR</string> </item>
    <item key="baz"> <string>BAZ</string> </item>
  </dictionary>
</pickle>
187 @@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
  <entry name="folder" keytype="__builtin__.str"
         type="OFS.Folder.Folder" factory="OFS.Folder.Folder" id="/folder" />
</entries>
0 folder/
0 folder/@@Zope/
159 folder/@@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
</entries>
"""
        self.assertFalse('folder2' in self.app.objectIds())

        self.publish('/@@checkin.snarf?note=test&name=folder2&src=folder',
                     basic='manager:asdf',
                     request_method='POST',
                     env={'CONTENT_TYPE': 'application/x-snarf'},
                     stdin=StringIO.StringIO(snarf),
                     handle_errors=False)

        folder2 = self.app['folder2']
        self.assertTrue(hasattr(folder2, 'foo'))
        self.assertEqual('FOO', folder2.foo)
        self.assertTrue(hasattr(folder2, 'bar'))
        self.assertEqual('BAR', folder2.bar)
        self.assertTrue(hasattr(folder2, 'baz'))
        self.assertEqual('BAZ', folder2.baz)

    def test_roundtrip(self):
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('foo', 'bar')
        self.app['folder'].a = 'asdf'
        self.app['folder'].b = 'bsdf'
        response = self.publish(
            '/folder/@@toFS.snarf', basic='manager:asdf')

        self.assertFalse('folder2' in self.app.objectIds())
        self.publish('/@@checkin.snarf?note=test&name=folder2&src=folder',
                     basic='manager:asdf',
                     request_method='POST',
                     env={'CONTENT_TYPE': 'application/x-snarf'},
                     stdin=StringIO.StringIO(response.getBody()),
                     handle_errors=False)

        self.assertEqual('<Folder at /folder2>', repr(self.app['folder2']))
        self.assertEqual('asdf', self.app['folder2'].a)
        self.assertEqual('bsdf', self.app['folder2'].b)
        self.assertEqual('<File at /folder2/foo>',
                         repr(self.app['folder2']['foo']))
        self.assertEqual('bar', self.app['folder2']['foo'].data)


class PickleOrderTest(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure element order in XML pickles is kept stable.

    """

    layer = gocept.fssyncz2.testing.functional_layer

    def setUp(self):
        super(PickleOrderTest, self).setUp()
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_entries_xml_should_have_a_stable_sorting_order(self):
        for i in xrange(32):
            self.app.manage_addFolder('folder')
            creation_order = list('abcdef')
            random.shuffle(creation_order)
            for key in creation_order:
                self.app['folder'].manage_addFile(key, 'foo')
            response = self.publish(
                '/folder/@@toFS.snarf', basic='manager:asdf')
            self.assertEquals("""\
  <entry name="a"
  <entry name="b"
  <entry name="c"
  <entry name="d"
  <entry name="e"
  <entry name="f"
""", grep('<entry', unsnarf(response, 'folder/@@Zope/Entries.xml')))
            self.app.manage_delObjects(['folder'])

    def test_objects_should_have_a_stable_attribute_sorting_order(self):
        for i in xrange(32):
            self.app._setObject('object', OFS.SimpleItem.SimpleItem())
            creation_order = list('abcdef')
            random.shuffle(creation_order)
            for key in creation_order:
                setattr(self.app['object'], key, 'foo')
            response = self.publish(
                '/object/@@toFS.snarf', basic='manager:asdf')
            self.assertEquals("""\
          <key> <string>a</string> </key>
          <key> <string>b</string> </key>
          <key> <string>c</string> </key>
          <key> <string>d</string> </key>
          <key> <string>e</string> </key>
          <key> <string>f</string> </key>
""", grep('<key>', unsnarf(response, 'root')))
            self.app.manage_delObjects(['object'])

    def test_folder_should_have_a_stable_attribute_sorting_order(self):
        # We test a folder's attribute serialisation specifically because we
        # reimplement folder serialisation for Zope2 and have actually seen
        # attribute serialisation for folders break at one point.
        for i in xrange(32):
            self.app.manage_addFolder('folder')
            creation_order = list('abcdef')
            random.shuffle(creation_order)
            for key in creation_order:
                setattr(self.app['folder'], key, 'foo')
            response = self.publish(
                '/folder/@@toFS.snarf', basic='manager:asdf')
            self.assertEquals("""\
      <key> <string>a</string> </key>
      <key> <string>b</string> </key>
      <key> <string>c</string> </key>
      <key> <string>d</string> </key>
      <key> <string>e</string> </key>
      <key> <string>f</string> </key>
""", grep('<key>', unsnarf(response, '@@Zope/Extra/folder/attributes')))
            self.app.manage_delObjects(['folder'])


class EncodingTest(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure pieces of non-ASCII text are readable and editable on disk.

    """

    layer = gocept.fssyncz2.testing.functional_layer

    def setUp(self):
        super(EncodingTest, self).setUp()
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_string_encoding(self):
        self.app._setObject('object', OFS.SimpleItem.SimpleItem())
        self.app['object'].foo = '\xf6'
        response = self.publish('/object/@@toFS.snarf', basic='manager:asdf')
        self.assert_('<string encoding="string_escape">\\xf6</string>' in
                     response.getBody())

    def test_string_encoding_cdata(self):
        self.app._setObject('object', OFS.SimpleItem.SimpleItem())
        self.app['object'].foo = '<\xf6&>'
        response = self.publish('/object/@@toFS.snarf', basic='manager:asdf')
        self.assert_('<string encoding="string_escape"><![CDATA[<\\xf6&>]]></string>' in
                     response.getBody())

    def test_string_encoding_cdata_ampersand(self):
        self.app._setObject('object', OFS.SimpleItem.SimpleItem())
        self.app['object'].foo = 'asdf&'
        response = self.publish('/object/@@toFS.snarf', basic='manager:asdf')
        self.assert_('<string><![CDATA[asdf&]]></string>' in
                     response.getBody())

    def test_unicode_encoding(self):
        self.app._setObject('object', OFS.SimpleItem.SimpleItem())
        self.app['object'].foo = u'\xf6'
        response = self.publish('/object/@@toFS.snarf', basic='manager:asdf')
        self.assert_('<unicode encoding="unicode_escape">\\xf6</unicode>' in
                     response.getBody())

    def test_unicode_encoding_cdata(self):
        self.app._setObject('object', OFS.SimpleItem.SimpleItem())
        self.app['object'].foo = u'<\xf6&>'
        response = self.publish('/object/@@toFS.snarf', basic='manager:asdf')
        self.assert_('<unicode encoding="unicode_escape"><![CDATA[<\\xf6&>]]></unicode>' in
                     response.getBody())

    def test_no_newline_escape(self):
        self.app._setObject('object', OFS.SimpleItem.SimpleItem())
        self.app['object'].foo = """Line 01
Line 02
Line 03"""
        response = self.publish('/object/@@toFS.snarf', basic='manager:asdf')
        self.assert_('<string>Line 01\nLine 02\nLine 03</string>' in
                     response.getBody())


class BaseFileSystemTests(Testing.ZopeTestCase.FunctionalTestCase):

    layer = gocept.fssyncz2.testing.server_layer

    def setUp(self):
        Testing.ZopeTestCase.ZopeTestCase.setUp(self)
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

        # initial data structure
        self.app.manage_addFolder('base')
        self.app['base'].manage_addFolder('sub')
        self.app['base'].manage_addFile('foo', 'Content of foo')
        self.app['base'].manage_addFile('bar', 'Content of bar')
        self.app['base']['sub'].manage_addFile('baz', '')
        import tempfile
        self.repository = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.repository)

    def _clean_checkin(self, opts, args):
        # XXX: checkin raises an Error. This should not happen.
        import zope.fssync.fsutil
        try:
            zope.app.fssync.main.checkin(opts, args)
        except zope.fssync.fsutil.Error:
            pass

    def _get_file_content(self, path):
        xml = open('%s/%s' % (self.repository, path), 'r').read()
        return pyquery.PyQuery(lxml.etree.fromstring(xml))

    def _read_file_content(self, path):
        pq = self._get_file_content(path)
        return pq('item[key=data] string')[0].text

    def _write_file_content(self, path, content):
        pq = self._get_file_content(path)
        setattr(pq('item[key=data] string')[0], 'text', content)
        xml = '<?xml version="1.0" encoding="utf-8" ?>\n%s' % (
            lxml.etree.tostring(pq[0]))
        return open('%s/%s' % (self.repository, path), 'w').write(xml)


class UserFolderTest(BaseFileSystemTests):

    def test_userfolder_is_not_duplicated_after_checkout_checkin(self):
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addProduct['OFSP'].manage_addUserFolder()
        import transaction
        transaction.commit()
        self.assertTrue(self.app['folder'].__allow_groups__.aq_base is
                        self.app['folder']['acl_users'].aq_base)

        import zope.app.fssync.main
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/folder' % self.layer.port,
            self.repository])
        self.assertNotEquals(len(os.listdir(self.repository)), 0)
        self.app._delObject('folder')
        self._clean_checkin([], [
            'http://manager:asdf@localhost:%s/folder' % self.layer.port,
            '%s/folder' % self.repository])
        self.assertTrue(self.app['folder'].__allow_groups__.aq_base is
                        self.app['folder']['acl_users'].aq_base)


class RoundTripTest(BaseFileSystemTests):
    """Test the data integrity during checkout, commit, update and checkin."""

    def test_checkout(self):
        # checkout the repository and check the data integrity
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            self.repository])
        self.assertEquals(os.listdir(self.repository), ['base', '@@Zope'])
        self.assertEquals(os.listdir('%s/base' % self.repository),
                          ['sub', 'bar', 'foo', '@@Zope'])
        self.assertEquals(os.listdir('%s/base/sub' % self.repository),
                          ['baz', '@@Zope'])

    def _add_flag(self, base_path, file, flag):
        meta_path = '%s/%s/@@Zope/Entries.xml' % (self.repository, base_path)
        xml = lxml.etree.fromstring(open(meta_path, 'r').read())
        pq = pyquery.PyQuery(xml)
        if pq('entry[name=%s]' % file):
            pq('entry[name=%s]' % file)[0].set('flag', flag)
        else:
            xml.append(lxml.etree.fromstring("""
                <entry name="%(name)s"
                  keytype="__builtin__.str"
                  type="OFS.Image.File"
                  id="/%(path)s/%(name)s"
                  flag="%(flag)s"
                />""" % dict(name=file, path=base_path, flag=flag)))
        open(meta_path, 'w').write(lxml.etree.tostring(xml))

    def test_commit(self):
        # test that changes to a file are committed to the database and
        # that files are added and deleted
        self.assertEquals(self.app['base']['bar'].data, 'Content of bar')
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            self.repository])
        # change the content of bar
        self._write_file_content('base/bar', 'asdf')
        # add baz
        baz_template = open(os.path.join(
            os.path.dirname(gocept.fssyncz2.__file__), 'testdata', 'baz'))
        open('%s/base/baz' % self.repository, 'w').write(baz_template.read())
        self._add_flag('base', 'baz', 'added')
        # delete foo
        os.remove('%s/base/foo' % self.repository)
        self._add_flag('base', 'foo', 'removed')
        zope.app.fssync.main.commit([], ['%s/base' % self.repository])
        self.assertEquals(self.app['base']['bar'].data, 'asdf')
        self.assertEquals(self.app['base']['baz'].data, 'Content of baz')
        self.assertRaises(KeyError, self.app['base'].__getitem__, 'foo')

    def test_update(self):
        # test that changes to file are updated to the repository and
        # that files are added and deleted
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            self.repository])
        # change the content of foo
        self.assertEquals(
            self._read_file_content('base/foo'), 'Content of foo')
        # delete bar
        self.app['base']._delObject('bar')
        self.app['base']['foo'].data = 'asdf'
        # add baz in base
        self.app['base'].manage_addFile('baz', 'Content of baz')
        # update
        zope.app.fssync.main.update([], ['%s/base' % self.repository])
        self.assertEquals(
            self._read_file_content('base/foo'), 'asdf')
        self.assertRaises(IOError, self._read_file_content, 'base/base')
        self.assertEquals(
            self._read_file_content('base/baz'), 'Content of baz')

    def test_checkin(self):
        # test a clean checkin
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            self.repository])
        self.app._delObject('base')
        self.assertRaises(KeyError, self.app.__getitem__, 'base')
        self._clean_checkin([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            '%s/base' % self.repository])
        self.assertEquals(self.app['base']['foo'].data, 'Content of foo')
        self.assertEquals(self.app['base']['bar'].data, 'Content of bar')
        self.assertEquals(self.app['base']['sub']['baz'].data, '')


class SanityCheckTest(BaseFileSystemTests):
    """Some sanity checks for checkout, commit, update and checkin."""

    def _checkout_checkin(self):
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            self.repository])
        self.layer.tearDown()
        self.layer.setUp()
        self._clean_checkin([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            '%s/base' % self.repository])
        transaction.commit()

    def test_checkout_checkin_amount_of_objects_equal(self):
        import testing
        import zope.component
        import ZODB.DemoStorage
        zope.component.provideAdapter(
            testing.FileStorageOIDs,
            (ZODB.DemoStorage.DemoStorage, ),
            testing.IOIDLoader)
        transaction.commit()
        initial_items = list(iter(testing.DatabaseIterator(self.app._p_jar)))
        self.assertEquals(len(initial_items), 12)
        self._checkout_checkin()
        new_items = list(iter(testing.DatabaseIterator(self.app._p_jar)))
        self.assertEquals(len(initial_items), len(new_items))

    def test_repositories_are_equal_after_checkout_checkin_checkout(self):
        def parse_cmpdir_output(dir):
            # path to the folder
            path = '/'.join(dir.left.split('/')[2:])
            # files, which are only in one folder
            diff_folder = dir.left_only + dir.right_only
            # files, which are in both folders, but which have diff. content
            diff_files = dir.diff_files
            data = [dict(path=path,
                         diff_folder=diff_folder,
                         diff_files=diff_files)]
            for subdir in dir.subdirs.values():
                data.extend(parse_cmpdir_output(subdir))
            return data

        # create second repository
        import tempfile
        self.repository2 = tempfile.mkdtemp()

        # checkout in first repository
        self._checkout_checkin()

        # check that repositories do not match
        import filecmp
        folder_stats = parse_cmpdir_output(
            filecmp.dircmp(self.repository, self.repository2))
        self.assertEquals(len(folder_stats), 1)
        stat = folder_stats[0]
        self.assertEquals(stat['diff_files'], [])
        self.assertEquals(stat['diff_folder'], ['@@Zope', 'base'])

        # checkout in second repository
        zope.app.fssync.main.checkout([], [
            'http://manager:asdf@localhost:%s/base' % self.layer.port,
            self.repository2])

        # check that both repositories match
        folder_stats = parse_cmpdir_output(
            filecmp.dircmp(self.repository, self.repository2))
        self.assertEquals(len(folder_stats), 16)
        for stat in folder_stats:
            self.assertEquals(stat['diff_files'], [])
            self.assertEquals(stat['diff_folder'], [])


def test_suite():
    return unittest.TestSuite(
        (unittest.makeSuite(Zope2ObjectsTest),
         unittest.makeSuite(ViewTests),
         unittest.makeSuite(FolderTest),
         unittest.makeSuite(PickleOrderTest),
         unittest.makeSuite(EncodingTest),
         unittest.makeSuite(ReferencesTest),
         unittest.makeSuite(UserFolderTest),
         unittest.makeSuite(RoundTripTest),
         unittest.makeSuite(SanityCheckTest),
         doctest.DocTestSuite('gocept.fssyncz2.folder'),
         ))
