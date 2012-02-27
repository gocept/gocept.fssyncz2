# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

from setuptools import setup
from setuptools import find_packages


setup(name='gocept.fssyncz2',
      version='1.5.1',
      author='gocept gmbh & co. kg',
      author_email='mail@gocept.com',
      description='zope.app.fssync integration for Zope2',
      url='http://pypi.python.org/pypi/gocept.fssyncz2',
      long_description=(
        open('README.txt').read() +
        '\n\n' +
        open('CHANGES.txt').read()),
      packages=find_packages('src'),
      include_package_data=True,
      package_dir={'': 'src'},
      license='ZPL 2.1',
      namespace_packages=['gocept'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Framework :: ZODB',
          'Framework :: Zope2',
          'Intended Audience :: Developers',
          'License :: OSI Approved',
          'License :: OSI Approved :: Zope Public License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.4',
          'Programming Language :: Python :: 2.5',
          'Topic :: Database',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Topic :: Utilities',
          ],
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
