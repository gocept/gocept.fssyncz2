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
import os.path


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


class FileSystemTreeTest(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure the file-system tree maps the object tree correctly.

    """

    layer = gocept.fssyncz2.testing.server_layer

    def setUp(self):
        Testing.ZopeTestCase.ZopeTestCase.setUp(self)
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('file', 'foo')
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])


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


class TestCommit(zope.fssync.tests.test_task.TestCheckClass):

    def setup_fssyncz2_changes(self):
        # provide gocept.fssyncz2 adapters
        import zope.component
        zope.component.provideAdapter(
            gocept.fssyncz2.pickle_.UnwrappedPickler)
        zope.component.provideAdapter(
            gocept.fssyncz2.traversing.OFSPhysicallyLocatable)

        # provide adapters for test directories and files
        zope.component.provideUtility(
            gocept.fssyncz2.folder.FolderSynchronizer,
            zope.fssync.interfaces.ISynchronizerFactory,
            zope.fssync.synchronizer.dottedname(
                gocept.fssyncz2.testing.PretendContainer))
        zope.component.provideUtility(
            gocept.fssyncz2.testing.FileSynchronizer,
            zope.fssync.interfaces.ISynchronizerFactory,
            name = zope.fssync.synchronizer.dottedname(
                gocept.fssyncz2.testing.ExampleFile))

        # create an initial database and repository structure
        self.base = gocept.fssyncz2.testing.PretendContainer()
        self.basedir = self.tempdir()

    def test_new_file_is_added_to_database(self):
        self.setup_fssyncz2_changes()

        # add a new file to the repo
        self.file2_path = os.path.join(self.basedir, 'file2.txt')
        open(self.file2_path, 'w').write('test')
        entry = self.getentry(self.file2_path)
        entry["path"] = "/parent/file2.txt"
        entry["factory"] = "gocept.fssyncz2.testing.ExampleFile"

        # file is not in the database
        self.assertRaises(KeyError, self.base.__getitem__, 'file2.txt')

        # commit changes in repo (add the file to the db)
        committer = gocept.fssyncz2.Commit(
            gocept.fssyncz2.getSynchronizer,
            self.checker.repository)
        committer.perform(self.base, "", self.basedir)

        # file is added and has content
        self.assertEquals(
            self.base['file2.txt'].data, 'test')

    def test_file_changes_commit_to_the_database(self):
        self.setup_fssyncz2_changes()
        # add a file which is changed in the test
        self.example_file = self.base['file.txt'] = (
            gocept.fssyncz2.testing.ExampleFile())
        self.file_path = os.path.join(self.basedir, 'file.txt')
        entry = self.getentry(self.file_path)
        entry["path"] = "/parent/file.txt"
        entry["factory"] = "fake factory name"

        # write content to file in repo
        self.writefile('new date', self.file_path)

        # file has content, database not
        self.assertEquals(
            open(self.file_path, 'r').readline(), 'new date')
        self.assertEquals(
            self.base['file.txt'].data, '')

        # commit changes in repo
        committer = gocept.fssyncz2.Commit(
            gocept.fssyncz2.getSynchronizer,
            self.checker.repository)
        committer.perform(self.base, "", self.basedir)

        # database is updated
        self.assertEquals(
            open(self.file_path, 'r').readline(), 'new date')
        self.assertEquals(
            self.base['file.txt'].data, 'new date')


def test_suite():
    return unittest.TestSuite(
        (unittest.makeSuite(Zope2ObjectsTest),
         unittest.makeSuite(ViewTests),
         unittest.makeSuite(FileSystemTreeTest),
         unittest.makeSuite(FolderTest),
         unittest.makeSuite(PickleOrderTest),
         unittest.makeSuite(EncodingTest),
         unittest.makeSuite(ReferencesTest),
         unittest.makeSuite(TestCommit),
         doctest.DocTestSuite('gocept.fssyncz2.folder'),
         ))
