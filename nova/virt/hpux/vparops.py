__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""


class VParOps(object):

    def __init__(self):
        pass

    def list_instances(self):
        return []

    def get_info(self, instance):
        return {}

    def destroy(self, context, instance, network_info):
        pass

    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info=None, block_device_info=None):
        pass
