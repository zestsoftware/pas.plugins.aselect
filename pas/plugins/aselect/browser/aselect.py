import logging

from zope.component import getMultiAdapter
from zope.i18n import translate
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFPlone import PloneMessageFactory as PMF

from pas.plugins.aselect import config

logger = logging.getLogger('pas.plugins.aselect.browser.aselect')


class RedirectView(BrowserView):
    """Redirect to the root of the site.

    The only reason this browser view exists, is so that you can
    declare this as a secure app in your A-Select filter plugin,
    something like this:

    aselect_filter_add_secure_app "/plone/aselect-login" "APP_ID" "default"
    aselect_filter_add_secure_app "/plone/@@aselect-login" "APP_ID" "default"

    That means you get redirected to the A-Select server to login.
    When you come back, this view redirects you to the Plone Site
    root.

    Now we can also configure our plugin to only look for the aselect
    cookies when the url is this browser view; if we don't, then
    clever visitors can add an A-Select cookie themselves and get access.

    Note that only URLs that are defined as secure apps in the filter
    plugin config (or with the same string at the beginning) are
    protected in the sense that any rogue A-Select cookies get
    removed.

    Note that the normal case is that at the beginning of the __call__
    to this view:

    - We have an A-Select cookie,

    - our plugin has authenticated us and has added the command to
      create an __ac cookie in the request.RESPONSE object,

    - so the __ac cookie is not actually in the *current* request yet,
      but will only be in the next,

    - but since our plugin *has* authenticated us based on the
      A-Select cookie, we *are* reported as being a member by the
      plone_portal_state.
    """

    _template = ViewPageTemplateFile('aselect.pt')

    def __call__(self):
        # Add a status message, showing whether the login has
        # succeeded or not.
        status = IStatusMessage(self.request)
        pps = getMultiAdapter((self.context, self.request),
                              name='plone_portal_state')
        anonymous = pps.anonymous()
        if anonymous and not self.show_group_options():
            success = False
            msg = PMF(u"Login failed")
            msg = translate(msg, 'plone', context=self.request)
            status.addStatusMessage(msg, type='error')
        elif anonymous:
            success = False
        else:
            success = True
            msg = PMF(u"heading_you_are_now_logged_in",
                      default=u"You are now logged in")
            msg = translate(msg, 'plone', context=self.request)
            status.addStatusMessage(msg, type='info')

        if anonymous and self.request.cookies.get('aselectattributes'):
            success = False
            logger.debug("We have an A-Select cookie but are still anonymous.")
        if (not success) or self.request.get('noredirect'):
            # Show the template.  Manually adding '?noredirect=1' to
            # the url may be handy for debugging: this way you stay on
            # this url, which means you can inspect the cookies.
            return self._template()

        logger.debug('Redirecting to Plone Site root.')
        # We are only defined on the Plone Site root, so we can just
        # redirect to the context.
        self.request.RESPONSE.redirect(self.context.absolute_url())

    def show_group_options(self):
        """Show various groups that a user can choose to join?

        With the default code should always be False, but if you do
        some patches, you may end up as user getting the right to join
        more than one group also when you should have exactly one.  So
        in our template you are given a choice.

        But if we are already a user, then obviously we have managed
        to successfully login and create a new user and chosen a group
        previously.  So we should not get the option to chose an extra
        group.
        """
        pps = getMultiAdapter((self.context, self.request),
                              name='plone_portal_state')
        if not pps.anonymous():
            return False
        if not config.MUST_HAVE_EXACTLY_ONE_GROUP:
            return False
        if len(self.possible_group_ids()) <= 1:
            return False
        return True

    def possible_group_ids(self):
        plugin = getToolByName(self.context, 'acl_users').aselectpas
        credentials = plugin.extractCredentials(self.request)
        if not plugin.user_accepted(credentials):
            # A guest user may not log in, so we should not confuse him by
            # offering a choice for some groups.
            return []
        return plugin._get_group_ids_from_credentials(credentials)
