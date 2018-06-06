===============
gocept.fssyncz2
===============

This package provides Zope2 integration of zope.fssync/zope.app.fssync, that
is, the ability to dump and restore ZODB content to the filesystem (To that
end, it provides synchronisers for OFS folders and the like, and adapts the
Zope3-ish mechanisms of zope.app.fssync to work with the Zope2 publisher).

Its main use case is to keep code stored inside the ZODB in a source code
management system. Therefore, it tries to make the pickles that are written to
disk as readable as possible (e. g. by not using base64 encoding).

So far, it concentrates on the ``dump`` and ``load`` actions (which
overwrite their target completely), since merging changes between different
checkouts needs to be done via the SCM anyway. (zope.app.fssync offers several
other actions, such as ``update`` and ``commit``, that try to be smart when
both the ZODB and the filesystem dump have changed concurrently. While this is
fine as long as only one filesystem representation exists, the model breaks
down when several dumps need to be synchronized with each other -- it is highly
non-trivial to determine whose change really is the right one in that case, so
we recommend against using these actions at this point.)

Usage
=====

You'll need to load both the configure.zcml and overrides.zcml configuration
files.

gocept.fssyncz2 provides a console script called ``fssync`` which wraps the two
actions (``dump`` and ``load``) and allows to pass in all other
parameters (URLs, locations, credentials). This is meant to be generated (via
buildout for example), like this::

  [fssync]
  recipe = zc.recipe.egg:scripts
  eggs = gocept.fssyncz2
  extra-paths = ${zope2:location}/lib/python
  arguments = host='${instance:http-address}', folder='myfolder', credentials='${instance:user}', repository='${buildout:directory}/var/zodb-dump'

Then you can dump your ZODB to the configured filesystem location with
``bin/fssync dump`` and load the data stored on the filesystem into the
ZODB with ``bin/fssync load``.


Ignoring objects
================

If you want to exclude some objects from being dumped (e.g. user data that
changes often), create a "Restrucured Text Document" named
``fssync-dump-ignore`` in the parent folder. This file may contain one object
name per line that should be excluded from dumping.
