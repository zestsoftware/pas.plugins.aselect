# -*- coding: utf-8 -*-
"""
This module contains the tool of pas.plugins.aselect
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.5'

long_description = (
    '.. contents::\n\n' +
    read('CHANGES.rst')
    + '\n\n' +
    read('README.txt')
    + '\n\n' +
    read('docs', 'CREDITS.txt'))

tests_require = ['zope.testing']

setup(name='pas.plugins.aselect',
      version=version,
      description="PAS Plugin for authentication with A-Select",
      long_description=long_description,
      classifiers=[
          'Framework :: Plone',
          'Framework :: Plone :: 3.3',
          'Framework :: Plone :: 4.0',
          'Framework :: Plone :: 4.1',
          'Framework :: Plone :: 4.2',
          'Framework :: Plone :: 4.3',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          ],
      keywords='',
      author='Zest Software',
      author_email='info@zestsoftware.nl',
      url='https://github.com/zestsoftware/pas.plugins.aselect',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['pas', 'pas.plugins'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        # -*- Extra requirements: -*-
                        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      test_suite='pas.plugins.aselect.tests.test_docs.test_suite',
      entry_points="""
      # -*- entry_points -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
