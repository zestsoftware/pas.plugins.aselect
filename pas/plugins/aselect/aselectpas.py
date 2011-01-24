import logging

from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_users
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
import Products.PluggableAuthService.interfaces.plugins as plugininterfaces
from Products.CMFCore.utils import getToolByName

from pas.plugins.aselect.utils import parse_attribute_cookie
from pas.plugins.aselect import config

logger = logging.getLogger('aselectpas')
# set logging level on whatever zope configured for root logger
logger.setLevel(logging.getLogger().level)

manage_addAselectPasForm = PageTemplateFile(
    'www/aselectpasAdd', globals(),
    __name__='manage_addAselectPasForm')


def manage_addAselectPas(dispatcher, id, title=None, REQUEST=None):
    """Add a AselectPas to a Pluggable Auth SErvice user folder.

    We're mostly tested in the README.txt. We'll only test the redirection
    here for test coverage completeness.

    >>> class MockDispatcher:
    ...     def _setObject(self, id, obj):
    ...         pass
    ...     def absolute_url(self):
    ...         return 'here'
    >>> class MockRequestResponse(dict):
    ...     def redirect(self, somewhere):
    ...         print 'redirected'
    >>> dispatcher = MockDispatcher()
    >>> response = MockRequestResponse()
    >>> request = MockRequestResponse()
    >>> request['RESPONSE'] = response

    >>> manage_addAselectPas(dispatcher, 'a') # Nothing gets returned
    >>> manage_addAselectPas(dispatcher, 'a', REQUEST=request)
    redirected

    """

    obj = AselectPas(id, title)
    dispatcher._setObject(obj.getId(), obj)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
            '%s/manage_workspace'
            '?manage_tabs_message='
            'AselectPas+added.'
            % dispatcher.absolute_url())


class AselectPas(BasePlugin):
    """ PAS plugin for using authentication cookies from the Apache
        and using them without doubting.
    """

    meta_type = 'AselectPas'
    security = ClassSecurityInfo()

    security.declareProtected(manage_users, 'manage_map')
    manage_map = PageTemplateFile('www/cookieMap', globals())

    manage_options = (BasePlugin.manage_options[:1]
                      + ({'label': 'A-Select PAS Settings',
                          'action': 'manage_map'}, )
                      + BasePlugin.manage_options[1:])

    def __init__(self, id, title=None):
        self._id = self.id = id
        self.title = title

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """Extract credentials from cookie or 'request'

        We try to extract credentials from the A-select cookie here.

        """
        if not hasattr(request, 'cookies'):
            logger.debug("No cookies found.")
            return {}
        cookies = request.cookies
        aselect_cookie = cookies.get('aselectattributes')
        if not aselect_cookie:
            logger.debug("No aselectattributes cookie found.")
            return {}

        if not config.EXTRACT_ON_ALL_PATHS:
            # We only accept an aselect cookie when the request is for
            # plonesite/@@aselect-login and some variations.
            path_info = request.get('PATH_INFO', '')
            """
            # Might be something like:
            # '/VirtualHostBase/http/taresia:8090/VirtualHostRoot//rapucation/@@aselect-login'
            pos = path_info.find('VirtualHostRoot')
            if pos != -1:
                offset = path_info.find('VirtualHostRoot') + \
                    len('VirtualHostRoot')
                path_info = path_info[offset:]
            path_info = path_info.strip('/')
            try:
                # Turn 'test/@@testcookies' into '@@testcookies'
                # or 'test/foo/bar' into 'foo/bar'
                path = '/'.join(path_info.split('/')[1:])
            except IndexError:
                logger.debug("Not extracting info: path not big enough: %r",
                             path)
                return {}
            """
            path_is_accepted = False
            for accepted in config.ACCEPTED_PATHS:
                if path_info.endswith(accepted):
                    path_is_accepted = True
                    break
            if not path_is_accepted:
                logger.debug("Not extracting info: not an accepted path: %r",
                             path_info)
                return {}

        # Parse the cookie.
        result = self._parseAttributeCookie(aselect_cookie)
        # Get the canonical user_id and store it in the credentials:
        user_id = self._get_user_id_from_credentials(result)
        result['user_id'] = user_id
        result['login'] = user_id
        logger.debug("Found aselectattributes cookie with user id %s",
                     user_id)
        return result

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """ Here we check the credentials and return a user if we are
            authenticated by Apache cookies.
        """
        extractor = credentials.get('extractor', 'none')
        if extractor != 'aselectpas':
            return None
        logger.debug("Credentials extracted by %s for request url: %s",
                     extractor, self.REQUEST.getURL())

        # Find a user_id.
        user_id = self._get_user_id_from_credentials(credentials)
        if not user_id:
            logger.debug("No user id found, so no authentication.")
            return None
        logger.debug("aselect user id found: '%s'." % user_id)

        if not self.user_accepted(credentials):
            logger.warn("User %r with given name %r not accepted.", user_id,
                        credentials.get('givenName', ''))
            return None

        # Login name and user id are usually the same.  Let's see if
        # we have a separate login name in the credentials anyway.
        login_name = credentials.get('login', user_id)

        if not config.UPDATE_AUTHENTICATED_USER and \
                self.REQUEST.cookies.get('__ac', None) is not None:
            logger.debug("Not updating user info.")
        else:
            logger.debug("Creating or updating user.")
            result = self._create_or_update_user(credentials)
            if not result:
                logger.warn("Creating or updating user failed.")
                return
            # Create plone.session __ac cookie.  Note that this only takes
            # effect during the *NEXT* request.
            pas = self._getPAS()
            pas.updateCredentials(self.REQUEST, self.REQUEST.response,
                                  login=user_id, new_password=None)
            logger.debug("Updated credentials of user %s, who should have "
                         "gotten an __ac cookie for authentication during "
                         "the next request.", user_id)

        # Return user id and login name; this makes the user
        # authenticated for the current request.
        logger.debug("Authenticated user id %s, login name %s",
                     user_id, login_name)
        return (user_id, login_name)

    def _get_user_id_from_credentials(self, credentials):
        """Get the user id from the credentials.

        Method has been added so make it easier to override the
        default behaviour.  Obvious choices are to either return the
        'uid' or the 'nlEduPersonRealId' from the credentials.

        And we may want to do some cleanup.

        And the calling method may choose to store the result in the
        credentials itself, as a cheap and easy way to avoid
        recalculating it every time.

        """
        user_id = credentials.get('user_id', None)
        if user_id is not None:
            # This is the cleaned up version already, so we return it
            # immediately.
            return user_id
        user_id = credentials.get('nlEduPersonRealId')
        if not user_id:
            user_id = credentials.get('uid')
        if not user_id:
            return ''

        # Get rid of any spaces.
        if user_id.find(' ') != -1:
            original = user_id
            user_id = original.replace(' ', '%20')
            logger.debug(
                "Removed spaces from aselect username: '%s' -> '%s'.",
                original, user_id)
        # And lowercase the username as edupoort apparently
        # randomizes the case.
        user_id = user_id.lower()
        return user_id

    def _get_group_ids_from_credentials(self, credentials):
        """Get group ids from the credentials.

        By default we look at the nlEduPersonHomeOrganizationId key,
        but the attribute id can be set in the config.

        Returns a list, though we usually expect just one group.
        """
        group_id = credentials.get(config.GROUP_ATTRIBUTE)
        if not group_id:
            return []
        return [group_id]

    def _filter_group_ids(self, group_ids):
        """Filter out not accepted group ids.

        For example, we may not want to add a user to the
        Administrators group.
        """
        if not group_ids:
            return []
        pas = self._getPAS()
        existing_group_ids = pas.getGroupIds()
        filtered_group_ids = []
        for group_id in group_ids:
            if not group_id:
                # Hm, empty
                continue
            if group_id not in existing_group_ids:
                continue
            if group_id in config.NOT_ACCEPTED_GROUPS:
                continue
            filtered_group_ids.append(group_id)
        return filtered_group_ids

    def _update_groups(self, user, group_ids):
        """Add this user to a group if needed.
        """
        current_group_ids = user.getGroupIds()
        new_group_ids = [group_id for group_id in group_ids
                         if group_id not in current_group_ids]
        logger.debug("Current groups: %s, new groups: %r",
                     current_group_ids, new_group_ids)
        if not new_group_ids:
            return

        user_id = user.getId()
        group_tool = getToolByName(self, 'portal_groups')
        for group_id in new_group_ids:
            logger.debug("Adding user id %s to group %s",
                         user_id, group_id)
            group_tool.addPrincipalToGroup(user_id, group_id)

    def _create_user(self, user_id):
        """Create user.

        User should not already exist.
        """
        portal_reg = getToolByName(self, 'portal_registration')

        # The password for the created user is never actually
        # used, but we should have one anyway.  Also, it should
        # not be a dummy easy one as then everyone who guesses
        # this can login as everyone.
        password = portal_reg.generatePassword()

        # We expect the user_id to have an '@' sign in it, which is
        # not allowed as Plone user id by default.  Since the user
        # cannot influence this, the cleanest is to allow the user_id
        # this one time.  This avoids the need for a patch at
        # import time, and prevents problems when someone edits
        # the allowed pattern in the ZMI.
        if not portal_reg._ALLOWED_MEMBER_ID_PATTERN.match(user_id):
            original_pattern = portal_reg.member_id_pattern
            portal_reg.manage_editIDPattern(user_id)
        else:
            original_pattern = None
        # If the next call raises an exception, this will get
        # caught by PAS, which will happily continue and will
        # later commit our possible change to the
        # member_id_pattern.  That is not good...
        try:
            portal_reg.addMember(user_id, password)
        except:
            if original_pattern is not None:
                # Restore original member id pattern
                portal_reg.manage_editIDPattern(original_pattern)
            # This reraises the original exception:
            raise
        # Too bad we don't have try/except/finally in python2.4.
        if original_pattern is not None:
            # Restore original member id pattern
            portal_reg.manage_editIDPattern(original_pattern)

    def _create_or_update_user(self, credentials):
        """Create or update user.

        When there is no user with this user_id in Plone, create it.

        When there is, update it.

        Return False in case of problems, True otherwise (creation or
        update succeeded or was not necessary).
        """
        user_id = self._get_user_id_from_credentials(credentials)
        # Search for Plone user with the given user id
        pas = self._getPAS()
        user = pas.getUserById(user_id)
        if user is None:
            logger.debug("User '%s' does not exist.", user_id)
            existing_user = False
        else:
            logger.debug("User '%s' already exists ", user_id)
            existing_user = True
            if not config.UPDATE_EXISTING_USERS:
                logger.debug("Not updating existing user.")
                return True

        # Get valid and accepted group ids.
        group_ids = self._get_group_ids_from_credentials(credentials)
        group_ids = self._filter_group_ids(group_ids)
        if config.MUST_HAVE_GROUP and not group_ids:
            logger.debug("User %r must have a group, but none found.", user_id)
            return False
        if not config.MUST_HAVE_EXACTLY_ONE_GROUP:
            groups_can_be_updated = True
        else:
            if len(group_ids) != 1:
                logger.debug("User %r must have exactly one group, but %d "
                             "found: %r.", user_id, len(group_ids), group_ids)
                groups_can_be_updated = False
            else:
                # If an existing user is sneaky enough, he can become
                # a member of two groups/schools.  We avoid that by
                # only listening to a group preference when the user
                # does not exist yet.
                if existing_user and \
                        self.REQUEST.get('preferred_group_id', ''):
                    groups_can_be_updated = False
                else:
                    groups_can_be_updated = True

        user_changed = False
        if not existing_user:
            if not groups_can_be_updated:
                logger.debug("Not creating new user, as groups cannot be "
                             "updated.")
                return False
            self._create_user(user_id)
            user = pas.getUserById(user_id)
            user_changed = True
        else:
            # Check if there are property changes.  We do this by
            # comparing the key/value pairs of the credentials with
            # the properties of the user.  Some properties don't exist
            # for a user, for example 'extractor'; they are
            # effectively ignored.
            for key, value in credentials.iteritems():
                if user.getProperty(key, value) != value:
                    user_changed = True
                    break

        # See if we need to add this user to a group.
        if group_ids:
            if groups_can_be_updated:
                self._update_groups(user, group_ids)
            else:
                logger.debug("Not updating groups of user %r.", user_id)

        # Now update properties if needed.
        if not user_changed:
            logger.debug("No change to existing user '%s'", user_id)
            return True

        logger.debug("Updating user_id '%s'", user_id)
        # Any non-existing properties get ignored in the setProperties call:
        user.setProperties(**credentials)
        logger.debug("Updated properties of user %s", user_id)
        return True

    def _parseAttributeCookie(self, cookiestring):
        """Parse the attribute cookie.
        """
        return parse_attribute_cookie(cookiestring)

    def user_accepted(self, credentials):
        """Filter out some users that we do not want.

        By default we check if the given name (first name) is in a
        black list.

        Returns True when we accept the user, False when not.
        """
        given_name = credentials.get('givenName', '')
        if not given_name:
            return True
        given_name = given_name.lower()
        return given_name not in config.NOT_ACCEPTED_USERS


classImplements(
    AselectPas,
    plugininterfaces.IAuthenticationPlugin,
    plugininterfaces.IExtractionPlugin,
    )

InitializeClass(AselectPas)
