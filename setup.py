# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

from setuptools import setup
from setuptools import find_packages


setup(name='gocept.fssyncz2',
      version='1.2',
      author='gocept gmbh & co. kg',
      author_email='mail@gocept.com',
      description='zope.app.fssync integration for Zope2',
      long_description=(
        open('README.txt').read() +
        '\n\n' +
        open('CHANGES.txt').read()),
      packages=find_packages('src'),
      include_package_data=True,
      package_dir={'': 'src'},
      license='ZPL 2.1',
      namespace_packages=['gocept'],
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zope.app.fssync',
          'zope.component',
          'zope.fssync',
          'zope.i18nmessageid',
          'zope.security',
          'zope.traversing',
          'zope.xmlpickle',
#          'Zope2',
          ],
      extras_require=dict(test=[
          'lxml',
          'pyquery',
          ]),
      entry_points=dict(console_scripts=[
          'fssync = gocept.fssyncz2.main:main'
          ]),
      )
