__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""

from nova import exception
from nova.virt.hpux import hostops
from nova.virt.hpux import utils
from oslo.config import cfg

hpux_opts = [
    cfg.StrOpt('username',
               default='root',
               help='Username for ssh command'),
    cfg.StrOpt('password',
               default='root',
               help='Password for ssh command'),
    cfg.StrOpt('ignite_ip',
               default='192.168.172.52',
               help='IP for ignite server'),
    ]

CONF = cfg.CONF
CONF.register_opts(hpux_opts, 'hpux')


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
