from pas.plugins.aselect import utils


def import_various(context):
    if context.readDataFile('pas_plugins_aselect_various.txt') is None:
        return
    portal = context.getSite()
    utils.add_aselectpas(portal)
