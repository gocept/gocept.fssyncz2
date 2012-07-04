##############################################################################
#
# CookieUserFolder   A cookie-enabled standard user folder for Zope
#
# This software is governed by a license. See
# LICENSE.txt for the terms of this license.
#
###############################################################################

__doc__ = """ CookieUserFolder Module """
__version__ = '$Revision: 1.9 $'[11:-2]

import urllib
import string
from base64 import encodestring, decodestring

import Products
from OFS.ObjectManager import ObjectManager
from Acquisition import aq_inner, aq_parent
from AccessControl.ZopeSecurityPolicy import _noroles
from AccessControl.User import UserFolder, BasicUserFolder
from Globals import DTMLFile, InitializeClass, package_home, MessageDialog


class CookieUserFolder(ObjectManager, UserFolder):
    """CookieUserFolder

    The CookieUserFolder is a user folder replacement for Zope.
    It works just like the bog-standard Zope user folder but uses
    cookie-based authentication and login/logout forms instead of
    basic HTTP authentication.
    """

    id = 'acl_users'
    title = 'Cookie User Folder'
    meta_type = 'Cookie User Folder'
    isAUserFolder = 1

    manage_contents = DTMLFile('dtml/contents', globals())
    manage = manage_main = BasicUserFolder._mainUser
    docLogin = DTMLFile('dtml/login', globals())
    docLogout = DTMLFile('dtml/logout', globals())

    manage_options = (
                ({'label': 'Custom Forms', 'action': 'manage_contents',
                  'help': ('CookieUserFolder', 'custom_forms.stx')},)
                + BasicUserFolder.manage_options)

    # This must stay accessible to everyone
    def validate(self, request, auth='', roles=_noroles):
        """ Validation using Cookies """
        req_has = request.has_key
        resp = request['RESPONSE']
        has_cookie = '__ac' in request.keys()
        login_doc = getattr(self, 'login', self.docLogin)
        v = request['PUBLISHED']  # the published object
        a, c, n, v = self._getobcontext(v, request)

        if has_cookie:    # Do we have the cookie?
            cookie = request['__ac']
            cookie = urllib.unquote(cookie)

            try:
                cookie = decodestring(cookie)
                name, password = tuple(string.split(cookie, ':'))
            except:
                resp.expireCookie('__ac', path='/')
                raise 'LoginRequired', login_doc(self, request)

        elif req_has('__ac_name') and req_has('__ac_password'):
            name = request['__ac_name']
            password = request['__ac_password']

            try:
                del request['__ac_name']
                del request['__ac_password']
            except:
                pass

        else:
            name, password = self.identify(auth)

        login_status = self.getLoginStatus()
        if login_status == 'LOCKED':
            return None
        elif login_status == 'CAPTCHA':
            # validated = request.SESSION.get('captcha_validated')
            captcha = request.get('__ac_captcha')
            expected = request.SESSION.get('captcha_word')
            # if not validated and (not captcha or captcha != expected):
            if (not captcha or captcha != expected):
                return None
            # request.SESSION.set('captcha_validated', True)

        user = self.authenticate(name, password, request)

        # user will be None if we can't authenticate him or if we can't find
        # his username in this user database.
        if user is not None:
            emergency = self._emergency_user

            if emergency and user is emergency:
                if self._isTop():
                    # we do not need to authorize the
                    # emergency user against the
                    # published object.
                    if not has_cookie:
                        token = '%s:%s' % (name, password)
                        token = encodestring(token)
                        token = urllib.quote(token)

                        resp.setCookie('__ac', token, path='/')

                    return emergency.__of__(self)

                else:
                    # we're not the top-level user folder
                    return None

            else:
                # We found a user, his password was correct, and the user
                # wasn't the emergency user.  We need to authorize the user
                # against the published object.
                if self.authorize(user.__of__(self), a, c, n, v, roles):
                    if not has_cookie:
                        token = '%s:%s' % (name, password)
                        token = encodestring(token)
                        token = urllib.quote(token)

                        resp.setCookie('__ac', token, path='/')

                    return user.__of__(self)

                # That didn't work.  Try to authorize the anonymous user.
                elif (self._isTop() and
                       self.authorize(self._nobody.__of__(self),
                                      a, c, n, v, roles)):
                    return self._nobody.__of__(self)

                else:
                    raise 'LoginRequired', login_doc(self, request)

        else:
            # either we didn't find the username, or the user's password
            # was incorrect.  try to authorize and return the anonymous user.
            if self._isTop() and self.authorize(self._nobody.__of__(self),
                                                a, c, n, v, roles):
                return self._nobody.__of__(self)

            elif not self._isTop():
                # We cannot authorize the user and we are not toplevel
                if self.authorize(self._nobody, a, c, n, v, roles):
                    # This place can be visited by anonymous users
                    # Must hand off authentication because the
                    # current user could be someone legit and not
                    # just anonymous. Any user folder can deal with
                    # anonymous so that is not a problem
                    return None
                else:
                    # This place is not accessible by anonymous.
                    # Make a pathetic attempt at authenticating
                    # above me... :(
                    # This code *will* fail with multiple user
                    # folders above this one. WAAA!
                    parent = aq_parent(aq_inner(self))
                    grandparent = aq_parent(aq_inner(parent))
                    acl = getattr(grandparent, 'acl_users', None)

                    if acl is None:
                        # This should never happen
                        raise 'LoginRequired', login_doc(self, request)

                    else:
                        user = acl.authenticate(name, password, request)

                        if user is None:
                            raise 'LoginRequired', login_doc(self, request)

                        if not has_cookie:
                            token = '%s:%s' % (name, password)
                            token = encodestring(token)
                            token = urllib.quote(token)

                            resp.setCookie('__ac', token, path='/')

                            return user.__of__(acl)

            else:
                # anonymous can't authorize or we're not top-level user folder
                raise 'LoginRequired', login_doc(self, request)

    def logOut(self, REQUEST):
        """ Force logout """
        logout_doc = getattr(self, 'logout', self.docLogout)
        REQUEST.RESPONSE.expireCookie('__ac', path='/')

        return logout_doc(self, REQUEST)

    def all_meta_types(self):
        """ What objects can be instantiated in me? """
        f = lambda x: x['name'] in ('DTML Method', 'DTML Document',
                                    'Script (Python)')

        return filter(f, Products.meta_types)


def manage_addCookieUserFolder(self, REQUEST=None):
    """ Called by Zope if you create a CookieUserFolder from the ZMI """

    if hasattr(self.aq_base, 'acl_users') and REQUEST is not None:
        return MessageDialog(title='Item Exists',
                             message='Object already contains a User Folder',
                             action='%s/manage_main' % REQUEST['URL1'])

    cuf = CookieUserFolder()
    self = self.this()

    self._setObject(cuf.getId(), cuf)
    self.__allow_groups__ = cuf

    if REQUEST is not None:
        msg = 'Cookie User Folder created'
        return self.manage_main(self, REQUEST)

InitializeClass(CookieUserFolder)
