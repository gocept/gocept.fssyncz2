import Missing
import gocept.fssyncz2
import pickle
import unittest


class Zope2ObjectsTest(unittest.TestCase):
    """Make sure that we can handle Zope2's Missing objects.

    """

    def test_missing_value(self):
        try:
            pickle.dumps({'foo': Missing.Value})
        except TypeError, e:
            self.fail(e)
        self.assert_("(dp0\nS'foo'\np1\nNs.",
                     repr(pickle.dumps({'foo': Missing.Value})))


def test_suite():
    return unittest.makeSuite(Zope2ObjectsTest)
