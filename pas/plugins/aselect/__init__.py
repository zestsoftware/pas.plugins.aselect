from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from aselectpas import AselectPas
from aselectpas import manage_addAselectPasForm
from aselectpas import manage_addAselectPas

registerMultiPlugin(AselectPas.meta_type)
# Commented out the following code as the tests don't exercize it and it
# doesn't appear to be necessary. [reinout]
#try:
#    registerMultiPlugin(AselectPas.meta_type)
#except RuntimeError:
#    # ignore exceptions on re-registering the plugin
#    pass


def initialize(context):
    """ Initialize the aselectpas plugin """

    context.registerClass(AselectPas,
                          permission=add_user_folders,
                          constructors=(manage_addAselectPasForm,
                                        manage_addAselectPas),
                          icon='www/aselect.png',
                          visibility=None)
