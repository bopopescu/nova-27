__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""

from nova import exception
from nova.virt.hpux import hostops
from nova.virt.hpux import utils
from oslo.config import cfg

CONF = cfg.CONF


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
        for npar in npar_list:
            cmd_for_npar = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': npar['ip_addr'],
                'command': '/opt/hpvm/bin/vparstatus'
            }
            exec_result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_npar)
            #Vpar status 'RunState' at location (row 3, column 3) in the
            #returned string exec_result
            retult = exec_result.strip().split('\n', 3)[2]
            if retult.split()[2] is 'UP':
                vpar_names.append(retult.split()[1])

        return vpar_names

    def get_info(self, instance):
        pass

    def destroy(self, context, instance, network_info):
        #power off the vpar before vparremove
        exec_result = None
        try:
            cmd_for_destroy = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': instance['host'],
                'command': '/opt/hpvm/bin/vparreset -p ' +
                           instance['display_name'] + ' -d -f'
            }
            exec_result = utils.ExecRemoteCmd().\
                exec_remote_cmd(**cmd_for_destroy)
            # delete a vPar
            # vparremove -p <vpar_name> -f
            if exec_result != None:
                cmd_for_destroy = {
                    'username': CONF.hpux.username,
                    'password': CONF.hpux.password,
                    'ip_address': instance['host'],
                    'command': '/opt/hpvm/bin/vparremove -p ' +
                               instance['display_name'] + ' -f'
                 }
            exec_result = utils.ExecRemoteCmd().exec_remote_cmd(
                **cmd_for_destroy)
        except utils.ExceptionPexpect as e:
            raise exception.Invalid(("Destroy instance error UNKNOWN"))
        finally:
            return exec_result

    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info=None, block_device_info=None):
        pass
