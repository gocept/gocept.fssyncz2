# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import Products.PythonScripts.PythonScript
import gocept.fssyncz2.pickle_
import zope.component


no_code_marker = object()


class Pickler(gocept.fssyncz2.pickle_.UnwrappedPickler):

    zope.component.adapts(Products.PythonScripts.PythonScript.PythonScript)

    def dump(self, writeable):
        _code = self.context.__dict__.pop('_code', no_code_marker)
        try:
            super(Pickler, self).dump(writeable)
        finally:
            pass
            if _code is not no_code_marker:
                self._code = _code


def setstate(self, state):
    state.setdefault('_code', None)
    orig_setstate(self, state)
    self._compile()


orig_setstate = Products.PythonScripts.PythonScript.PythonScript.__setstate__
Products.PythonScripts.PythonScript.PythonScript.__setstate__ = setstate
