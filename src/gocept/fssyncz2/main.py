# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
import sys
import zope.app.fssync.main


def checkinout(host, folder, credentials, repository):
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
        sys.stderr.write('Usage: %s <checkin|checkout>\n' % sys.argv[0])
        sys.exit(1)

    command = sys.argv[1]

    url = 'http://%s@%s' % (credentials, host)

    if command == 'checkout':
        command = zope.app.fssync.main.checkout
    elif command == 'checkin':
        command = zope.app.fssync.main.checkin
        repository = os.path.join(repository, folder)
    else:
        raise ValueError('Invalid command %r' % command)

    command([], [os.path.join(url, folder), repository])
