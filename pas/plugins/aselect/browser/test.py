import logging

from Products.Five.browser import BrowserView

from pas.plugins.aselect import config
from pas.plugins.aselect.utils import parse_attribute_cookie
from pas.plugins.aselect.utils import make_cookie_string


logger = logging.getLogger('cookietest')


class TestCookiesView(BrowserView):
    """ a view to set some cookies to test the A-Select PAS plugin

    From the latest documentation, it looks like these keys are always
    given in the aselectattributes cookie:

    uid
    nlEduPersonRealId
    givenName
    nlEduPersonTussenvoegsels
    sn
    mail
    eduPersonAffiliation
    nlEduPersonHomeOrganizationId
    nlEduPersonHomeOrganization
    initials
    homePhone
    mobile
    homePostalAddress


    Interesting for us seems to be:
    - fullname = givenName + nlEduPersonTussenvoegsels + sn
    - mail
    - nlEduPersonHomeOrganizationId (looks like BRIN-code, can be used
      to add the user to a group, also see config.GROUP_ATTRIBUTE)

    Example from the documentation:

    aselectattributes=PR_achternaam=Vries&nlEduPersonTussenvoegsels=de&sn=Vries

    Split on the ampersand:

    DL_AANB01_taal=Nederlands
    DL_AANB01_taal_2=Frans
    PR_achternaam=Vries
    PR_email=j.devries%40school.nl
    PR_entreeid=EF7849639
    PR_tussenvoegsel=de
    PR_voornaam=Jan
    eduPersonAffiliation=affiliate
    givenName=jan
    mail=j.devries%40school.nl
    nlEduPersonHomeOrganization=Entree
    nlEduPersonHomeOrganizationId=ENTREE
    nlEduPersonTussenvoegsels=de
    sn=Vries
    uid=jdvries%40kennisnet.org
    """

    cookiename = 'aselectattributes'
    # These are the attributes we are interested in:
    attributes = config.ASELECT_ATTRIBUTES

    def update(self):
        request = self.context.REQUEST
        response = request.RESPONSE
        form = request.form
        keys = form.keys()
        if 'clearcookies' in keys:
            response.expireCookie(self.cookiename)
            msg = 'aselect cookie cleared'
            logger.debug(msg)
            return msg
        # Note that clearing the __ac cookie has no effect if you
        # still have an aselect cookie, as the authentication code
        # sets the __ac cookie again, so two conflicting cookie
        # instructions would end up in the same request.  Removing
        # both at the same time does not work either.
        if 'submit' not in keys:
            # Do nothing.
            return

        value = make_cookie_string(**form)
        response.setCookie(self.cookiename, value)
        return '%s cookie set to value %s' % (self.cookiename, value)

    def value_for(self, field):
        """Give the value for the field (attribute).

        1. Get it from the request.
        2. Get it from the cookie.
        3. Empty.
        """
        if not self.request.get('clearcookies'):
            from_req = self.request.get(field, None)
            if from_req is not None:
                return from_req
        cookie_string = self.request.cookies.get(self.cookiename, None)
        if cookie_string is None:
            return ''
        cookie_dict = parse_attribute_cookie(cookie_string)
        return cookie_dict.get(field, '')

    def update_authenticated_user(self):
        return config.UPDATE_AUTHENTICATED_USER
