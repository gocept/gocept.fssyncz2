#
#   ReplaceUserFolder    Replace a standard Zope user folder with
#                        a Cookie User Folder and retain all user 
#                        accounts
#

import string
from Products.CookieUserFolder.CookieUserFolder import manage_addCookieUserFolder
from Acquisition import aq_base

log = []

def replace( self ):

    self.REQUEST.RESPONSE.setHeader( 'Content-type', 'text/html' )
    
    # Find the user folder in this folder
    old_acl = getattr( aq_base( self ), 'acl_users', None )

    if old_acl is None:
        err_msg = _formatMessage( 'Cannot find a user folder here!' )
        return err_msg

    if old_acl.meta_type != 'User Folder':
        err_msg = _formatMessage( 'Cannot convert this user folder' )
        return err_msg

    
    log.append( '- Step 1: Found user folder' )


    old_users = old_acl.data
    log.append( '- Step 2: Retrieving existing user accounts' )

    self._delObject( 'acl_users' )
    log.append( '- Step 3: Deleting old user folder' )

    manage_addCookieUserFolder( self )
    log.append( '- Step 4: Adding new user folder' )

    new_acl = self.acl_users
    new_acl.data = old_users
    log.append( '- Step 5: Storing old user data in new user folder' )
    
    log.append( 'Done!' )

    log_msg = _formatMessage( log )

    return log_msg


def _formatMessage( message ):

    if type( message ) == type( [] ):
        message = string.join( log, '\n' )

    return '<pre>%s</pre>' % message
