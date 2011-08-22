import unittest

from Products.Five import fiveconfigure
try:
    from Zope2.App import zcml
except ImportError:
    # BBB for Plone 3, Zope 2.10
    from Products.Five import zcml

from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Testing import ZopeTestCase as ztc
from zope.component import testing
from zope.testing import doctest
from zope.testing import doctestunit

import pas.plugins.aselect

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


@onsetup
def load_package_products():
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml',
                     pas.plugins.aselect)
    ptc.installPackage('pas.plugins.aselect')
    fiveconfigure.debug_mode = False

load_package_products()
ptc.setupPloneSite(products=['pas.plugins.aselect'])


def test_suite():
    return unittest.TestSuite([
        # Unit tests
        doctestunit.DocTestSuite(
            module='pas.plugins.aselect.aselectpas',
            setUp=testing.setUp, tearDown=testing.tearDown),

        # Integration tests that use PloneTestCase
        ztc.FunctionalDocFileSuite(
            'README.txt', package='pas.plugins.aselect',
            optionflags=OPTIONFLAGS,
            test_class=ptc.FunctionalTestCase),
        ztc.FunctionalDocFileSuite(
            'browser.txt', package='pas.plugins.aselect',
            optionflags=OPTIONFLAGS,
            test_class=ptc.FunctionalTestCase),

        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
