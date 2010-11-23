import Missing
import OFS.SimpleItem
import Testing.ZopeTestCase
import doctest
import gocept.fssyncz2.testing
import pickle
import random
import unittest
import urllib2
import zope.testbrowser.browser


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


class CheckoutTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure checkout doesn't fail with Zope2.

    """

    layer = gocept.fssyncz2.testing.server_layer

    def setUp(self):
        Testing.ZopeTestCase.ZopeTestCase.setUp(self)
        self.app.manage_addFolder('folder')
        self.app['folder'].manage_addFile('file', 'foo')
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_remove_security_proxies(self):
        browser = zope.testbrowser.browser.Browser()
        browser.addHeader('Authorization',
                          'Basic '+'manager:asdf'.encode('base64'))
        try:
            browser.open(
                'http://localhost:%s/folder/@@toFS.snarf' % self.layer.port)
        except urllib2.HTTPError, e:
            self.fail(e)


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
        self.assert_("""\
folder/@@Zope/Entries.xml
<?xml version='1.0' encoding='utf-8'?>
<entries>
  <entry name="foo"
         keytype="__builtin__.str"
         type="OFS.Image.File"
         id="/folder/foo"
         />
</entries>
""" in response.getBody())
        self.assert_("""\
folder/@@Zope/State
<?xml version="1.0" encoding="utf-8" ?>
<pickle>
  <initialized_object>
    <klass>
      <global name="__newobj__" module="copy_reg"/>
    </klass>
    <arguments>
      <tuple>
        <global name="Folder" module="OFS.Folder"/>
      </tuple>
    </arguments>
    <state>
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
        <item key="_objects">
            <tuple>
              <dictionary>
                <item key="id">
                    <string>foo</string>
                </item>
                <item key="meta_type">
                    <string>File</string>
                </item>
              </dictionary>
            </tuple>
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
    </state>
  </initialized_object>
</pickle>
""" in response.getBody())
        self.app.manage_delObjects(['folder'])


class PickleOrderTest(Testing.ZopeTestCase.FunctionalTestCase):
    """Make sure element order in XML pickles is kept stable.

    """

    layer = gocept.fssyncz2.testing.functional_layer

    def setUp(self):
        super(PickleOrderTest, self).setUp()
        self.app['acl_users']._doAddUser('manager', 'asdf', ('Manager',), [])

    def test_folder_entry_ordering(self):
        for i in xrange(32):
            self.app.manage_addFolder('folder')
            creation_order = list('abcdef')
            random.shuffle(creation_order)
            for key in creation_order:
                self.app['folder'].manage_addFile(key, 'foo')
            response = self.publish(
                '/folder/@@toFS.snarf', basic='manager:asdf')
            dump_lines = response.getBody().splitlines(True)
            self.assertEquals("""\
name="folder"
folder/@@Zope/Entries.xml
name="a"
name="b"
name="c"
name="d"
name="e"
name="f"
folder/a
folder/b
folder/c
folder/d
folder/e
folder/f
folder/@@Zope/State
""", ''.join(line[9:] for line in dump_lines
             if ' folder/' in line or '<entry name=' in line))
            self.app.manage_delObjects(['folder'])

    def test_attribute_ordering(self):
        for i in xrange(32):
            self.app._setObject('object', OFS.SimpleItem.SimpleItem())
            creation_order = list('abcdef')
            random.shuffle(creation_order)
            for key in creation_order:
                setattr(self.app['object'], key, 'foo')
            response = self.publish(
                '/object/@@toFS.snarf', basic='manager:asdf')
            dump_lines = response.getBody().splitlines(True)
            self.assertEquals("""\
        <item key="__ac_local_roles__">
              <item key="test_user_1_">
        <item key="_owner">
          <key> <string>a</string> </key>
          <key> <string>b</string> </key>
          <key> <string>c</string> </key>
          <key> <string>d</string> </key>
          <key> <string>e</string> </key>
          <key> <string>f</string> </key>
""", ''.join([line for line in dump_lines if 'key' in line][1:]))
            self.app.manage_delObjects(['object'])

    def test_attribute_ordering_for_folder(self):
        # We test a folder's attribute serialisation specifically because we
        # reimplement folder serialisation for Zope2 and have actually seen
        # attribute serialisation for folders break at one point.
        for i in xrange(32):
            self.app.manage_addFolder('object')
            creation_order = list('abcdef')
            random.shuffle(creation_order)
            for key in creation_order:
                setattr(self.app['object'], key, 'foo')
            response = self.publish(
                '/object/@@toFS.snarf', basic='manager:asdf')
            dump_lines = response.getBody().splitlines(True)
            self.assertEquals("""\
          <key> <string>a</string> </key>
          <key> <string>b</string> </key>
          <key> <string>c</string> </key>
          <key> <string>d</string> </key>
          <key> <string>e</string> </key>
          <key> <string>f</string> </key>
""", ''.join([line for line in dump_lines if '<key>' in line]))
            self.app.manage_delObjects(['object'])


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


def test_suite():
    return unittest.TestSuite(
        (unittest.makeSuite(Zope2ObjectsTest),
         unittest.makeSuite(CheckoutTests),
         unittest.makeSuite(FolderTest),
         unittest.makeSuite(PickleOrderTest),
         unittest.makeSuite(EncodingTest),
         doctest.DocTestSuite('gocept.fssyncz2.folder'),
         ))
