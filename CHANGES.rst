=======
Changes
=======


1.8 (unreleased)
================

- Nothing changed yet.


1.7 (2018-09-19)
================

- Fix restore of PluggableAuthService user folder.

- Stabilised a test that depends on a file object's etag to have a
  deterministic length. (#10491)


1.6 (2013-03-22)
================

- Don't dump the co_varnames attribute of PythonScripts as it is neither
  stable nor needed in the dump.


1.5.2 (2012-07-04)
==================

- Add workaround for CookieUserFolder to restore the ``__allow_groups__``
  pointer after load when fssync-ignoring it (#11111).


1.5.1 (2012-02-27)
==================

- Made ignore mechanism actually ignore objects on loading a dump. (#10488)


1.5 (2012-02-23)
================

- Add ignore mechanism (#10483).


1.4 (2011-11-28)
================

- Fixed a bug which prevented strings containing the sequence ]]> from being
  dumped and loaded back, giving rise to ill-formed XML pickles.

- Cleaned up a little: removed an unused testdata directory.


1.3 (2011-08-05)
================

- Pinned all used versions in buildout.

- Added trove classifiers to package meta data.


1.2 (2011-04-10)
================

- Made sure that newlines inside strings end up as newlines instead of ``\n``
  notation in XML pickles (fixes #8860).

- Install the fssync script in the development buildout.

- When dumping a PythonScript, leave out its _code attribute to reduce noise
  in the XML pickles (fixes #8859).

- Declared dependency on `zope.i18nmessageid`.

- Better error message when finding persistent objects in Extras.`


1.1 (2011-01-31)
================

- Renamed console commands to dump/load instead of checkout/checkin to avoid
  confusion with SCM operations.


1.0 (2011-01-31)
================

- Initial release.
