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
        co_varnames = self.context.func_code.co_varnames
        del self.context.func_code.co_varnames
        try:
            super(Pickler, self).dump(writeable)
        finally:
            if _code is not no_code_marker:
                self._code = _code
            self.co_varnames = co_varnames


def setstate(self, state):
    state.setdefault('_code', None)
    state.setdefault('co_varnames', ())
    orig_setstate(self, state)
    self._compile()


orig_setstate = Products.PythonScripts.PythonScript.PythonScript.__setstate__
Products.PythonScripts.PythonScript.PythonScript.__setstate__ = setstate
