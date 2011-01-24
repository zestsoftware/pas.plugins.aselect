PAS plugin for A-Select integration
===================================

`A-Select`_ (Dutch only) in combination with the "licentiekantoor"
("license office"), is a full authentication/authorization
solution. It can be compared a bit to openid: with the addition of
authorization.

Basic premise: the already-available apache configuration handles the
communication with aselect and ensures that the aselect cookies that we get
are genuine. So the PAS plugin only has to deal with the cookie contents.

.. _`A-Select`: http://entree.kennisnet.nl/


PAS functionality
-----------------

This plugin does extraction and authentication:

* Extract credentials from the ``aselectattributes`` cookie: the user
  id and member data, like fullname, email address, organization id
  (BRIN code).

* Authenticate credentials: create or update a member object based on
  the extracted credentials and authenticate this user.

* If the organization id matches the id of an existing group, we add
  this user to that group.  Note that groups are never removed again.


Note on performance and up-to-date-ness
---------------------------------------

We could check for changes in the user properties or the groups based
on the cookie on each request.  But each request does not only mean
once for each page, but also once for each css, javascript or image
file.  This might be bad for performance (though it is probably
doable).

So, our solution is to only extract aselect info on certain paths; by
default this done on the `@@aselect-login' path and the
`@@testcookies`` path.  Alternatively you may choose to never update
the aselect info for users that already have an
authentication cookie (__ac) from plone.session.  A logout should be
enough to reset the plone.session cookie, which should trigger a
renewed automatic login plus getting the property updates, because the
A-Select cookie should still be available.

That is the default behaviour.  In ``config.py`` you can change several
settings (in a patch in an own package) if you do not like the
defaults and are aware of the effects on performance and
up-to-date-ness.  Note that the ``config.py`` is reasonably well
commented, so if you are a programmer you may want to have a look at that.

Alternatively, we might want to do something smart, like remembering
the cookiestring somewhere and only trying an update if there is a
change in that string.


Usage
-----

Tested with Plone 3.3.5.  Add ``pas.plugins.aselect`` to the eggs
parameter of your instance section in buildout.cfg.  Rerun buildout,
start your instance, and install the plugin through 'Add/Remove
Products' in the Site Setup.  The only thing the install code does, is
add the plugin to acl_users, activate it for the required plugin
interfaces, and make sure it is the first plugin listed for those
interfaces (the order might not be that important actually, see
above).  So if wanted, you could do that manually.


Note that in the README.txt within the pas/plugins/aselect directory,
there is an extensive doctest.  It probably works better as test than
as documentation, so it is not included on the PyPI page.
