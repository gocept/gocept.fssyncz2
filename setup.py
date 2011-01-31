from setuptools import setup
from setuptools import find_packages


setup(name='gocept.fssyncz2',
      version='1.0dev',
      packages=find_packages('src'),
      include_package_data=True,
      package_dir={'': 'src'},
      namespace_packages=['gocept'],
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zope.app.fssync',
          'zope.component',
          'zope.fssync',
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
          'sync = gocept.fssyncz2.main:checkinout'
          ]),
      )
