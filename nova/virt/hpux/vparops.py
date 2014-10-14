__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""

from nova.virt.hpux import hostops


class VParOps(object):

    def __init__(self):
        pass

    def list_instances(self):
        """Get the up(running) vPar name list of all nPars.

        :returns: A list of up(running) vPar name
        """
        vpar_names = []
        # Here, we should get nPar list from db
        # to avoid frequent interaction with ignite server.
        #admin_context = context.get_admin_context()
        #npar_list = db.npar_get_all(admin_context)
        npar_list, vpar_list = hostops.HostOps()._get_client_list()
        for vpar in vpar_list:
            vpar_names.append(vpar['name'])
        return vpar_names

    def get_info(self, instance):
        return {}

    def destroy(self, context, instance, network_info):
        pass

    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info=None, block_device_info=None):
        pass
