# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
import sys
import zope.app.fssync.main
import gocept.fssyncz2.main


def main(host, folder, credentials, repository):
    """
    Wraps zope.app.fssync commands checkin and checkout,
    prepopulating all parameters.

    url: localhost:8080
    folder: myapp
    credentials: user:password
    repository: /path/to/fssync/repository

    Set up in a buildout like this:
    [scripts]
    recipe = zc.recipe.egg:scripts
    eggs = gocept.fssyncz2
    extra-paths = ${zope2:location}/lib/python
    arguments = host='${instance:http-address}', folder='myapp', repository='${buildout:directory}/dump', credentials='${instance:user}'
    """

    if len(sys.argv) != 2:
        sys.stderr.write('Usage: %s <dump|load>\n' % sys.argv[0])
        sys.exit(1)
    command = sys.argv[1]

    try:
        command = getattr(gocept.fssyncz2.main, command)
    except AttributeError:
        raise ValueError('Invalid command %r' % command)

    command(host, folder, credentials, repository)


def _get_url(host, credentials=None):
    if credentials is not None:
        credentials += '@'
    else:
        credentials = ''
    return 'http://%s%s' % (credentials, host)


def dump(host, folder, credentials, repository):
    zope.app.fssync.main.checkout(
        [], [os.path.join(_get_url(host, credentials), folder), repository])


def load(host, folder, credentials, repository):
    repository = os.path.join(repository, folder)
    zope.app.fssync.main.checkin(
        [], [os.path.join(_get_url(host, credentials), folder), repository])
