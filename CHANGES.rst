Changelog for pas.plugins.aselect
=================================


1.5 (2012-10-14)
----------------

- Moved to https://github.com/zestsoftware/pas.plugins.aselect
  [maurits]


1.4 (2011-08-22)
----------------

- Made tests a bit less likely to fail when config defaults have
  changed (like in a monkey patch in a client package).
  [maurits]


1.3 (2011-01-24)
----------------

- Moved to Plone collective.  First public release.
  [maurits]

- Fixed tests after recent addition of the UPDATE_EXISTING_USERS
  config option (default: False).
  [maurits]


1.2 (2010-08-30)
----------------

- Added locales for one translation.
  [maurits]

- On the @@aselect-login page, if no user has been created because he
  could belong to multiple groups, show options for the user to choose
  a group to join.
  [maurits]

- Added config option GROUP_ATTRIBUTE, with default
  'nlEduPersonHomeOrganizationId'
  [maurits]

- Added two config options: MUST_HAVE_GROUP and
  MUST_HAVE_EXACTLY_ONE_GROUP, both by default True.  Using these
  default settings, we refuse to create and authenticate a user when
  we cannot extract exactly one group from the credentials.
  [maurits]

- Added config option NOT_ACCEPTED_USERS and compare the given name of
  the credentials with this black list.  We do not authenticate a
  blacklisted user.
  [maurits]

- Renamed the ALWAYS_UPDATE configuration option to the clearer
  UPDATE_AUTHENTICATED_USER.
  [maurits]

- Renamed the EXTRACT_ALWAYS configuration option to the clearer
  EXTRACT_ON_ALL_PATHS.
  [maurits]

- Change config.UPDATE_ALWAYS to True, so we always update the user
  properties and group settings, as we by default just react on the
  aselect-login page and testcookies page anyway.
  [maurits]

- When we do not know a last name, add the first part of the email to
  the fullname instead (if that is known).
  [maurits]


1.1 (2010-08-25)
----------------

- Allow calling @@aselect-login?noredirect=1 to stay on the
  @@aselect-login page instead of being redirected to the Plone Site
  root.  This should make it easier to inspect cookies.
  [maurits]


1.0 (2010-08-19)
----------------

- Do not always extract and authenticate credentials, but only when on
  certain paths, like testcookies and aselect-login.
  [maurits]

- Added aselect-login page that simply redirects to the Plone Site
  root.  Define this as a protected app in the (Apache) A-Select
  module and you should be good to go.
  [maurits]

- If the nlEduPersonHomeOrganizationId (presumably a BRIN code)
  matches a group id, we add the user to that group during
  authentication.
  [maurits]

- Only deal with the aselectattributes cookie, not any others.
  [maurits]

- First release, based on some old customer code.
  [maurits]
