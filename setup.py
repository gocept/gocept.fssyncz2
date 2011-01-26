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
#          'Zope2',
          'zope.app.fssync',
	  'lxml',
          'pyquery',
          ],
      )
