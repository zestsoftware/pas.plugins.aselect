PAS plugin for A-Select integration
===================================

See the README.txt in the top level directory (next to setup.py) for
some general info.


Cookie contents
---------------

In this doctest the PAS plugin is mostly tested by accessing its
methods directly.  The main methods like extractCredentials and
authenticateCredentials expect a request object as parameter.  So we
create some classes to play with, making it easier to create a request
object that suites our needs:

    >>> class MockRequest:
    ...     cookies = {}
    >>> from pas.plugins.aselect.utils import make_cookie_string
    >>> class MockAselectRequest:
    ...     def __init__(self, **kwargs):
    ...         value = make_cookie_string(**kwargs)
    ...         self.cookies = {'aselectattributes': value}
    ...         # By default, we pretend to be on the testcookies page.
    ...         self.PATH_INFO = kwargs.get('PATH_INFO', '/plone/@@testcookies')
    ...     def get(self, name, default=None):
    ...         if name == 'PATH_INFO':
    ...             return self.PATH_INFO
    ...         raise NotImplementedError
    >>> anon_request = MockRequest()
    >>> member_request = MockAselectRequest()

There used to be four cookies, but now there is one cookie to rule
them all:

* aselectattributes holds a list of all kinds of attributes, most
  importantly the nlEduPersonRealId which will become the user id in
  Plone (with a fallback to the uid attribute).

    >>> 'aselectattributes' in anon_request.cookies
    False
    >>> 'aselectattributes' in member_request.cookies
    True

Items in the request that we are not interested in, get ignored:

    >>> request = MockAselectRequest()
    >>> request.cookies['aselectattributes']
    ''
    >>> request = MockAselectRequest(uid='Joris', whocares='no-one')
    >>> request.cookies['aselectattributes']
    'uid%3DJoris'


Let's test our mock classes with some real data, taken from the
documentation at
http://entree.kennisnet.nl/attachments/session=cloud_mmbase+1836441/Werking_van_Entree_v2.0_(nov_2008).pdf

    >>> data = dict(
    ...     DL_AANB01_taal='Nederlands',
    ...     DL_AANB01_taal_2='Frans',
    ...     PR_achternaam='Vries',
    ...     PR_email='j.devries@school.nl',
    ...     PR_entreeid='EF7849639',
    ...     PR_tussenvoegsel='de',
    ...     PR_voornaam='Jan',
    ...     eduPersonAffiliation='affiliate',
    ...     givenName='jan',
    ...     mail='j.devries@school.nl',
    ...     nlEduPersonHomeOrganization='Entree',
    ...     nlEduPersonHomeOrganizationId='ENTREE',
    ...     nlEduPersonTussenvoegsels='de',
    ...     sn='Vries',
    ...     uid='jdvries@kennisnet.org',
    ...     )
    >>> request = MockAselectRequest(**data)
    >>> cookie = request.cookies['aselectattributes']
    >>> cookie
    'givenName%3Djan%26uid%3Djdvries%40kennisnet.org%26nlEduPersonHomeOrganizationId%3DENTREE%26nlEduPersonTussenvoegsels%3Dde%26sn%3DVries%26mail%3Dj.devries%40school.nl'

If something is wrong in the above line it may be tricky to detect
where the difference is.  So we look at some individual items:

    >>> 'DL_AANB01_taal' in cookie
    False
    >>> 'DL_AANB01_taal_2' in cookie
    False
    >>> 'givenName%3Djan' in cookie
    True
    >>> 'mail%3Dj.devries%40school.nl' in cookie
    True
    >>> from pas.plugins.aselect import config
    >>> config.GROUP_ATTRIBUTE in cookie
    True
    >>> 'nlEduPersonHomeOrganizationId%3DENTREE' in cookie
    True
    >>> 'nlEduPersonTussenvoegsels%3Dde' in cookie
    True
    >>> 'sn%3DVries' in cookie
    True
    >>> 'uid%3Djdvries%40kennisnet.org' in cookie
    True

We can also parse the cookie, which makes it easier to read and adds
some more info like the full name and email instead of mail:

    >>> from pas.plugins.aselect.utils import parse_attribute_cookie
    >>> parsed = parse_attribute_cookie(cookie)
    >>> parsed.get('mail')
    'j.devries@school.nl'
    >>> parsed.get('email')
    'j.devries@school.nl'
    >>> parsed.get('fullname')
    'jan de Vries'
    >>> from pprint import pprint
    >>> pprint(parsed)
    {'email': 'j.devries@school.nl',
     'fullname': 'jan de Vries',
     'givenName': 'jan',
     'mail': 'j.devries@school.nl',
     'nlEduPersonHomeOrganizationId': 'ENTREE',
     'nlEduPersonTussenvoegsels': 'de',
     'sn': 'Vries',
     'uid': 'jdvries@kennisnet.org'}


PAS plugin introduction
-----------------------

With the cookie contents clear, we now have to integrate their data
into Plone's PAS Pluggable Authentication Service. PAS' functionality
is split up over multiple plugins. The `PAS reference manual
<http://plone.org/documentation/manual/pas-reference-manual>`_
provides a good overview.

We need two plugin types: extracting user data from the cookies and
authenticating with that data.

    >>> import Products.PluggableAuthService.interfaces.plugins
    >>> plugininterfaces = Products.PluggableAuthService.interfaces.plugins

An **extraction plugin** extracts the user ID from the cookie, a separate
**authentication plugin** tells PAS that the extracted ID is an authenticated
user.

Our plugin is already installed (done by the portal_quickinstaller):

    >>> plugin = self.portal.acl_users.aselectpas
    >>> plugin
    <AselectPas at /plone/acl_users/aselectpas>

Make sure trying to add a aselectpas on an object without any acl_users
fails.

    >>> from pas.plugins.aselect import utils
    >>> utils.add_aselectpas(object())
    Traceback (most recent call last):
      ...
    LookupError: No acl_users can be acquired or otherwise found

If we try to add it when it already exists, the adder should just silently do
nothing.

    >>> utils.add_aselectpas(self.portal)

Our plugin is listed in all relevant plugin categories:


    >>> from Products.PluggableAuthService.interfaces.plugins import \
    ...   IAuthenticationPlugin, IExtractionPlugin
    >>> pas = self.portal.acl_users
    >>> 'aselectpas' in pas.plugins.listPluginIds(IAuthenticationPlugin)
    True
    >>> 'aselectpas' in pas.plugins.listPluginIds(IExtractionPlugin)
    True

Note that aselectpas used to be the first plugin in categories, but
that is not actually needed.


User ID extraction
------------------

Test with empty and small aselectattributes cookies:

    >>> request = MockRequest()
    >>> plugin.extractCredentials(request)
    {}
    >>> request = MockAselectRequest(nlEduPersonRealId='reinout')
    >>> credentials = plugin.extractCredentials(request)
    >>> credentials['user_id']
    'reinout'
    >>> pprint(credentials)
    {'email': '',
     'fullname': '',
     'login': 'reinout',
     'nlEduPersonRealId': 'reinout',
     'user_id': 'reinout'}
   
Don't panic if there are no cookies in the request

    >>> class NoCookies:
    ...     pass
    >>> no_cookies = NoCookies()
    >>> plugin.extractCredentials(no_cookies)
    {}

The extraction plugin not only extracts the username, but also all
data from the cookie, and extras like fullname: handy as the extracted
credentials are passed to most/all other plugins.

    >>> data = dict(
    ...     givenName='Arthur',
    ...     mail='arthur.dent@example.com',
    ...     nlEduPersonHomeOrganizationId='company',
    ...     nlEduPersonTussenvoegsels='',
    ...     sn='Dent',
    ...     uid='dentarthurdent@hyperspace',
    ...     )
    >>> request = MockAselectRequest(**data)
    >>> credentials = plugin.extractCredentials(request)
    >>> credentials['user_id']
    'dentarthurdent@hyperspace'

Note that empty items like the nlEduPersonTussenvoegsels get ignored:

    >>> pprint(credentials)
    {'email': 'arthur.dent@example.com',
     'fullname': 'Arthur Dent',
     'givenName': 'Arthur',
     'login': 'dentarthurdent@hyperspace',
     'mail': 'arthur.dent@example.com',
     'nlEduPersonHomeOrganizationId': 'company',
     'sn': 'Dent',
     'uid': 'dentarthurdent@hyperspace',
     'user_id': 'dentarthurdent@hyperspace'}


Authentication
--------------

If the extraction plugin has not extracted an aselect UID, the authentication
plugin won't authenticate a thing.

    >>> credentials = {}
    >>> plugin.authenticateCredentials(credentials) is None
    True

By default we want all users to be a member of a group, otherwise we
do not accept them, so we also do not authenticate or create them.
This is signalled with the nlEduPersonHomeOrganizationId attribute.
(or config.GROUP_ATTRIBUTE).  So first we need to create a matching
group.

    >>> self.portal.portal_groups.addGroup('company')
    True

If the aselect username has been extracted, we'll return that as the
user's id and login name.  No further questions asked.  We have to
insert 'aselectpas' as the id of the extractor, otherwise the
credentials get ignored.  We will test a name with spaces in it while
we are at it:

    >>> credentials = {'uid': 'Pointy%20Haired Boss',
    ...                'nlEduPersonHomeOrganizationId': 'company',
    ...                'extractor': 'aselectpas'}
    >>> plugin.authenticateCredentials(credentials)
    ('pointy%20haired%20boss', 'pointy%20haired%20boss')

Note that the result is lowercase. We do that as aselect seems to randomly
switch between upper and lower case versions...

And some other weird characters are allowed in usernames too.  We will
test them all.  The rules by edupoort are: A-Z, a-z, 0-9 and "!@#-_.,"

    >>> username = "AZ!@#-09_.,az"
    >>> credentials = {'uid': username,
    ...                'givenName': 'Joe',
    ...                'nlEduPersonHomeOrganizationId': 'company',
    ...                'extractor': 'aselectpas'}
    >>> result = plugin.authenticateCredentials(credentials)
    >>> result[0] == result[1] == "az!@#-09_.,az"
    True

If there is an authentication cookie, we still authenticate (we used
to skip this step, but now we just do not update the properties/groups
of the user):

    >>> plugin.REQUEST.cookies['__ac'] = 'yes, I am authenticated'
    >>> result = plugin.authenticateCredentials(credentials)
    >>> result[0] == result[1] == "az!@#-09_.,az"
    True
    >>> del plugin.REQUEST.cookies['__ac']

And if the credentials have not been extracted by our own
'aselectpas' extractor, we will ignore it::

    >>> credentials = {'aselect_username': 'Pointy%20Haired Boss',
    ...                'nlEduPersonHomeOrganizationId': 'company',
    ...                'aselectnaw': '', 'extractor': 'plone.session'}
    >>> plugin.authenticateCredentials(credentials) is None
    True

Some users are blacklisted, for example users with a given name of
'Gastgebruiker' (guest user):

    >>> credentials = {'uid': 'guest',
    ...                'givenName': 'Gastgebruiker',
    ...                'extractor': 'aselectpas'}
    >>> plugin.authenticateCredentials(credentials) is None
    True
    >>> credentials = {'uid': 'guest',
    ...                'nlEduPersonHomeOrganizationId': 'company',
    ...                'givenName': 'Not a guest',
    ...                'extractor': 'aselectpas'}
    >>> plugin.authenticateCredentials(credentials)
    ('guest', 'guest')


Property extractions
--------------------

First we extract credentials again.  No member is added yet:

    >>> data = dict(
    ...     givenName='Arthur',
    ...     mail='arthur.dent@example.com',
    ...     nlEduPersonHomeOrganizationId='company',
    ...     nlEduPersonTussenvoegsels='',
    ...     sn='Dent',
    ...     uid='dentarthurdent@hyperspace',
    ...     )
    >>> request = MockAselectRequest(**data)
    >>> credentials = plugin.extractCredentials(request)
    >>> member = pas.getUserById('dentarthurdent@hyperspace')
    >>> member is None
    True

We set the extractor id manually.  Normally this is done automatically
by PAS, but we call our plugin directly so we have to do it manually
here:

    >>> credentials['extractor'] = 'aselectpas'

Then we need to authenticate:

    >>> plugin.authenticateCredentials(credentials)
    ('dentarthurdent@hyperspace', 'dentarthurdent@hyperspace')
    >>> member = pas.getUserById('dentarthurdent@hyperspace')
    >>> member is not None
    True

After we are authenticated, the properties should be available for the
user.  Note that our plugin used to be a property extraction plugin as
well, but not anymore.

    >>> member.getProperty('fullname')
    'Arthur Dent'
    >>> member.getProperty('email')
    'arthur.dent@example.com'

If there is a normal authentication cookie, we still authenticate, but do not
update the user properties (or group settings).  But this depends on
the UPDATE_AUTHENTICATED_USER setting (which has changed default at
least once) and now also UPDATE_EXISTING_USERS, so we change those
settings here:

    >>> from pas.plugins.aselect import config
    >>> orig_UPDATE_AUTHENTICATED_USER = config.UPDATE_AUTHENTICATED_USER
    >>> orig_UPDATE_EXISTING_USERS = config.UPDATE_EXISTING_USERS
    >>> config.UPDATE_AUTHENTICATED_USER = False
    >>> config.UPDATE_EXISTING_USERS = True
    >>> credentials['fullname'] = 'My second name'
    >>> plugin.authenticateCredentials(credentials)
    ('dentarthurdent@hyperspace', 'dentarthurdent@hyperspace')
    >>> member = pas.getUserById('dentarthurdent@hyperspace')
    >>> member.getProperty('fullname')
    'My second name'
    >>> plugin.REQUEST.cookies['__ac'] = 'yes, I am authenticated'
    >>> credentials['fullname'] = 'My third name'
    >>> plugin.authenticateCredentials(credentials)
    ('dentarthurdent@hyperspace', 'dentarthurdent@hyperspace')
    >>> member = pas.getUserById('dentarthurdent@hyperspace')
    >>> member.getProperty('fullname')
    'My second name'
    >>> del plugin.REQUEST.cookies['__ac']
    >>> credentials['fullname'] = 'Arthur Dent'
    >>> plugin.authenticateCredentials(credentials)
    ('dentarthurdent@hyperspace', 'dentarthurdent@hyperspace')
    >>> member = pas.getUserById('dentarthurdent@hyperspace')
    >>> member.getProperty('fullname')
    'Arthur Dent'

Restore config settings:

    >>> config.UPDATE_AUTHENTICATED_USER = orig_UPDATE_AUTHENTICATED_USER
    >>> config.UPDATE_EXISTING_USERS = orig_UPDATE_EXISTING_USERS


Group extraction
----------------

The 'aselectattributes' cookie contains information to match the user
to an organization.  This is done with the
nlEduPersonHomeOrganizationId attribute (see config.GROUP_ATTRIBUTE).
We expect to get a BRIN-code there, which is a unique id for a school.
If the group does not exist, we are not authenticated and the user
does not get created.

    >>> request = MockAselectRequest(uid='jorisslob',
    ...                              nlEduPersonHomeOrganizationId='BRIN01')
    >>> credentials = plugin.extractCredentials(request)
    >>> credentials['extractor'] = 'aselectpas'
    >>> plugin.authenticateCredentials(credentials) is None
    True
    >>> pas.getUserById('jorisslob') is None
    True

So we create a few groups:

    >>> self.portal.portal_groups.addGroup('BRIN01')
    True
    >>> self.portal.portal_groups.addGroup('BRIN01notexactly')
    True
    >>> self.portal.portal_groups.addGroup('BRIN02')
    True

For instruction, we check the result of some PAS and portal_groups methods:

    >>> len(pas.searchGroups(id='BRIN01'))
    2
    >>> len(pas.searchGroups(id='BRIN01', exact_match=True))
    1
    >>> self.portal.portal_groups.getGroupById('BRIN01')
    <GroupData at /plone/portal_groupdata/BRIN01 used for /plone/acl_users/source_groups>
    >>> self.portal.portal_groups.getGroupById('notgroupatall')

Now that our group exists, we try authenticating again:

    >>> plugin.authenticateCredentials(credentials)
    ('jorisslob', 'jorisslob')
    >>> member = pas.getUserById('jorisslob')
    >>> member.getGroups()
    ['AuthenticatedUsers', 'BRIN01']

Note that there is no code that automatically removes a group when the
aselectattributes cookie changes.  Someone may have been manually
added to another group and we do not want to stomp on that.


For the next tests we change the default config again:

    >>> orig_UPDATE_EXISTING_USERS = config.UPDATE_EXISTING_USERS
    >>> config.UPDATE_EXISTING_USERS = True

We make sure that users can not be made Administrator; in fact, by
default authentication will fail if we try that, as we want exactly
one accepted group:

    >>> credentials[config.GROUP_ATTRIBUTE] = 'Administrators'
    >>> plugin.authenticateCredentials(credentials) is None
    True
    >>> member = pas.getUserById('jorisslob')
    >>> member.getGroups()
    ['AuthenticatedUsers', 'BRIN01']

Nor Reviewer:

    >>> credentials[config.GROUP_ATTRIBUTE] = 'Reviewers'
    >>> plugin.authenticateCredentials(credentials)
    >>> member = pas.getUserById('jorisslob')
    >>> member.getGroups()
    ['AuthenticatedUsers', 'BRIN01']

But a different group does work:

    >>> credentials[config.GROUP_ATTRIBUTE] = 'BRIN02'
    >>> plugin.authenticateCredentials(credentials)
    ('jorisslob', 'jorisslob')
    >>> member = pas.getUserById('jorisslob')
    >>> member.getGroups()
    ['AuthenticatedUsers', 'BRIN02', 'BRIN01']

With two groups, we by default do not authenticate, nor create a
user.  We can only check that by overriding a method from our plugin:

    >>> from pas.plugins.aselect.aselectpas import AselectPas
    >>> ori_get_group_ids_from_credentials = AselectPas._get_group_ids_from_credentials
    >>> def new_get_group_ids_from_credentials(self, credentials):
    ...     return ['BRIN01', 'BRIN02']
    >>> AselectPas._get_group_ids_from_credentials = new_get_group_ids_from_credentials

Try it:

    >>> request = MockAselectRequest(uid='napoleon')
    >>> credentials = plugin.extractCredentials(request)
    >>> credentials['extractor'] = 'aselectpas'
    >>> plugin.authenticateCredentials(credentials) is None
    True
    >>> pas.getUserById('napoleon') is None
    True

Change the method to return just one group, which makes sure that our
attempt at overriding does actually work:

    >>> def new_get_group_ids_from_credentials(self, credentials):
    ...     return ['BRIN01']
    >>> AselectPas._get_group_ids_from_credentials = new_get_group_ids_from_credentials

And try again:

    >>> request = MockAselectRequest(uid='napoleon')
    >>> credentials = plugin.extractCredentials(request)
    >>> credentials['extractor'] = 'aselectpas'
    >>> plugin.authenticateCredentials(credentials)
    ('napoleon', 'napoleon')
    >>> member = pas.getUserById('napoleon')
    >>> member.getGroups()
    ['AuthenticatedUsers', 'BRIN01']

Restore the overriden method:

    >>> AselectPas._get_group_ids_from_credentials = ori_get_group_ids_from_credentials

And restore the config setting:

    >>> config.UPDATE_EXISTING_USERS = orig_UPDATE_EXISTING_USERS
