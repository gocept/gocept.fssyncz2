##############################################################################
#
# __init__.py	Initialization code for the CookieUserFolder
#
# This software is governed by a license. See
# LICENSE.txt for the terms of this license.
# 
##############################################################################

__doc__     = """ CookieUserFolder initialization module """
__version__ = '$Revision: 1.1 $'[11:-2]

from CookieUserFolder import CookieUserFolder, manage_addCookieUserFolder

def initialize(context):
    context.registerClass( CookieUserFolder
                         , permission='Add User Folders'
                         , constructors=( manage_addCookieUserFolder, )
                         , icon='www/CookieUserFolder.gif'
                         )

    context.registerHelp()
