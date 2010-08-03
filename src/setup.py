from setuptools import setup
from setuptools import find_packages


setup(name='gocept.fssyncz2',
      version='0.1',
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['gocept'],
      zip_safe=False,
      install_requires=[
          'setuptools',
#          'Zope2',
          'zope.app.fssync',
          ],
      )
