# -*- coding: utf-8 -*-
"""
This module contains the tool of pas.plugins.aselect
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.4dev'

long_description = (
    '.. contents::\n\n' +
    read('CHANGES.txt')
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
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        ],
      keywords='',
      author='Zest Software',
      author_email='info@zestsoftware.nl',
      url='http://svn.plone.org/svn/collective/PASPlugins/pas.plugins.aselect',
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
