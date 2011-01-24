# Note that the automatic tests take the definitions in this file as a
# given; there are no tests that change the settings here to see if it
# all still works as expected then.
#
# Potentially, these could become settings editable through the ZMI
# within the edit form of the plugin.

# These are the attributes given by A-SELECT that we are interested in:
ASELECT_ATTRIBUTES = [
    'uid',
    'nlEduPersonRealId',
    'givenName',
    'nlEduPersonTussenvoegsels',
    'sn',
    'mail',
    'nlEduPersonHomeOrganizationId',
    ]

# id of the group attribute; should be in ASELECT_ATTRIBUTES as well.
GROUP_ATTRIBUTE = 'nlEduPersonHomeOrganizationId'

# Should we always (that is, once for each and every request) update
# the user properties and the group memberships during authentication?
# The check we do is: is there is an __ac session cookie?  If
# UPDATE_AUTHENTICATED_USER is True, performance might be a bit lower.
#
# Note that it makes the most sense when from the two
# UPDATE_AUTHENTICATED_USER and EXTRACT_ON_ALL_PATHS settings, one is
# True and the other is False.
UPDATE_AUTHENTICATED_USER = True

# Should we update properties and groups of *existing* users at all?
UPDATE_EXISTING_USERS = False

# Should we extract info from the A-Select cookie for every url, or
# only for selected urls like @@aselect-login?  You may need to change
# the default based on which parts of your site are defined as a
# secure app for A-Select.
EXTRACT_ON_ALL_PATHS = False

# When EXTRACT_ON_ALL_PATHS is False, we only extract when the url starts
# with the Plone Site url + one of the paths here.  Note, this may not
# work nicely if your Plone Site is not directly in the Zope root for
# some strange reason.  You should make sure to only list paths here
# that are protected by your A-Select setup.
ACCEPTED_PATHS = [
    '/@@aselect-login',
    '/aselect-login',
    '/@@testcookies',
    '/testcookies',
    ]

# List of users that we do not accept, in lowercase.  By default, we
# compare this to the givenName attribute.
NOT_ACCEPTED_USERS = [
    'gastgebruiker',
    'gast',
    'guestuser',
    'guest',
    ]

# Some groups should not get users through A-Select.
NOT_ACCEPTED_GROUPS = [
    'Administrators',
    'Reviewers',
    'AuthenticatedUsers',
    ]

# Must the user have a group before being accepted?
MUST_HAVE_GROUP = True

# Must the user have *exactly one* group before being accepted? Adding
# a user to two groups might not be wanted.
MUST_HAVE_EXACTLY_ONE_GROUP = True
