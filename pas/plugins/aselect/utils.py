import cgi
import urllib

from Products.PluggableAuthService.interfaces import authservice

from pas.plugins.aselect.config import ASELECT_ATTRIBUTES


def add_aselectpas(context):
    """Finds the nearest acl_users and adds aselectpas-based plugins.
    These plugins are automatically activated as well.  Returns a tuple of all
    plugin instances created.

    Originally copied from apachepas. GPL, made by Rocky Burt for Zest
    Software.

    We had some code here previously that made sure our plugin was
    listed as the first everywhere.  But after careful consideration
    it was found this was not needed.  While PAS is getting the user
    ids from the request, it iterates over all extraction plugins; for
    all extracted credentials it iterates over all authentication
    plugins.  If our extraction and authentication succeeds, we add an
    __ac cookie which might be found by the plone.session
    authentication plugin, but this only happens during the NEXT
    request, so the order of plugins does not matter at all for us.
    """
    acl_users = getattr(context, 'acl_users', None)
    if acl_users is None:
        raise LookupError("No acl_users can be acquired or otherwise found")
    pas = authservice.IPluggableAuthService(acl_users)
    if hasattr(pas, 'aselectpas'):
        return

    setup = pas.manage_addProduct['pas.plugins.aselect']
    setup.manage_addAselectPas('aselectpas', 'AselectPas')

    aselectpas = pas['aselectpas']
    aselectpas.manage_activateInterfaces(
        ['IAuthenticationPlugin',
         'IExtractionPlugin',
         ])

    return (aselectpas, )


def parse_cookie(cookiestring):
    """Parse an extended cookie.

    Say the cookie is this:
    'PR_achternaam=Vries&nlEduPersonTussenvoegsels=de&sn=Vries&sn=Jansen'

    With cgi.parse_qs, we get a dictionary with lists as values:
    {'PR_achternaam': ['Vries'], 'nlEduPersonTussenvoegsels': ['de'],
     'sn': ['Vries', 'Jansen']}

    We return a cleaned up dictionary of this, with the string
    version of the first value, so:
    {'PR_achternaam': 'Vries', 'nlEduPersonTussenvoegsels': 'de',
     'sn': 'Vries'}

    Note that cgi.parse_qs removes any keys that have an empty value.
    """
    # The cookie may be urlencoded.  Probably a good idea to
    # unquote it.
    cookiestring = urllib.unquote_plus(cookiestring)
    tempdict = cgi.parse_qs(cookiestring)
    info = dict([(i, tempdict[i][0]) for i in tempdict])
    return info


def parse_attribute_cookie(cookiestring):
    """Parse the attribute cookie and add some items.

    Add email and fullname.
    """
    info = parse_cookie(cookiestring)
    email = info.get('mail', '')
    first_name = info.get('givenName', '')
    lastname_parts = [
        info.get('nlEduPersonTussenvoegsels'),
        info.get('sn'),
        ]
    last_name = ' '.join([part for part in lastname_parts if part])
    if last_name:
        fullname = first_name + " " + last_name
    elif email:
        # When first name is John and email is johndoe@example.org,
        # make the fullname 'John (johndoe)' to have a bit more clue
        # which of the five Johns in your class this person actually
        # is.
        email_name = email.split('@')[0]
        fullname = '%s (%s)' % (first_name, email_name)
    else:
        fullname = first_name

    # Add email and fullname to the info dict.
    info['email'] = email
    info['fullname'] = fullname
    return info


def make_cookie_string(**kwargs):
    """Turn keyword arguments into a cookie string.

    The resulting string can then be used as value for a cookie.  Case
    in point: the aselectattributes cookie has a rather long value
    like this:

    aselectattributes=PR_achternaam=Vries&nlEduPersonTussenvoegsels=de&sn=Vries

    We assume the values are strings.
    """
    values = []
    for key, value in kwargs.items():
        if key not in ASELECT_ATTRIBUTES:
            continue
        # Only '&' and '=' are dangerous for the value at this point.
        # The rest is taken care of later by quote_plus.
        value = value.replace('&', '%26')
        value = value.replace('=', '%3D')
        values.append('%s=%s' % (key, value))

    value = '&'.join(values)
    return urllib.quote_plus(value)
