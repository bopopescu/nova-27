__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""

import time

from nova import exception
from nova.virt.hpux import hostops
from nova.virt.hpux import utils
from oslo.config import cfg
#from nova import db

CONF = cfg.CONF


class VParOps(object):

    def __init__(self):
        pass

    def get_instance_host_name(self, ip_addr):
        # Will get the host name (napr_name) of given vpar reading from DB.
        pass

    def _get_vpar_resource_info(self, npar_name, ip_addr):
        """Get vPar resource info.

        :returns: A dict including CPU, memory and run state info.
        """
        vpar_info = {}
        cmd_for_vpar = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': ip_addr,
            'command': '/opt/hpvm/bin/vparstatus -p ' + npar_name + ' -v'
        }
        exec_result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_vpar)
        results = exec_result.strip().split('\n')
        for item in results:
            if 'RunState' in item:
                # item as 'RunState: UP'
                vpar_info['run_state'] = item.split(':')[1].strip()
            elif 'System assigned [Count]' in item:
                # item as 'System assigned [Count]:  5\r'
                vpar_info['CPU'] = int(item.split(':')[1].strip())
            elif 'Total Memory(MB)' in item:
                # item as 'Total Memory(MB):  2048\r'
                vpar_info['Total_memory'] = int(item.split(':')[1].strip())
            else:
                continue
        return vpar_info

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
            # Vpar status 'RunState' at location (row 3, column 3) in the
            # returned string exec_result
            retult = exec_result.strip().split('\n', 3)[2]
            if retult.split()[2] is 'UP':
                vpar_names.append(retult.split()[1])

        return vpar_names

    def get_info(self, instance):
        """Get status of given vPar instance.

        :returns: A dict including CPU, memory, disk info and
        run state of required vPar.
        """
        # This will be replaced since nPar_list will get by reading from
        # DB directly.
        napr_list, vpar_list = hostops.HostOps()._get_client_list()
        for vpar in vpar_list:
            if vpar['ip_addr'] is instance['ip_addr']:
                host_npar_name = self.get_host_name(vpar['ip_addr'])
                vpar_info = self._get_vpar_resource_info(host_npar_name,
                                                         vpar['ip_addr'])
        if not vpar_info:
            raise exception.VparNotFound(instance['name'])
        else:
            return vpar_info

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

    def define_dbprofile(self, prof_define_info):
        """Define dbprofile in EFI shell to prepare later vPar installing.
        :param: A dict contains all of the needed info for dbprofile define,
                - vPar name (vpar_name)
                - nPar IP address (ip_addr)
                - Ignite-UX server IP address (sip)
                - Ignite client IP address (cip)
                - Ignite client  server Gateway IP address (gip)
                - Ignite client  server Network mask (mask)
        :return: Name of defined profile if success.
        """
        prof_name = 'profile_hpux'
        #Hard code the Ignite-UX server IP address for now
        prof_define_info['sip'] = '192.168.172.51'
        try:
            cmd_for_dbprofile_define = {
                'username': CONF.hpux.username,
                'vpar_name': prof_define_info['vpar_name'],
                'ip_address': prof_define_info['ip_address'],
                'remote_command': '/opt/hpvm/bin/vparconsole -p ' +
                                  prof_define_info['vpar_name'],
                'efi_command': 'dbprofile -dn ' + prof_name + ' -sip ' +
                                  prof_define_info['sip'] + ' -cip ' +
                                  prof_define_info['cip'] + ' -gip ' +
                                  prof_define_info['gip'] + ' -m ' +
                                  prof_define_info['mask']
            }
            utils.ExecRemoteCmd.exec_efi_cmd(**cmd_for_dbprofile_define)
        except utils.ExceptionPexpect as e:
            raise exception.Invalid(("Failed to define dbprofile"))
        finally:
            if not e:
                return prof_name

    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info=None, block_device_info=None):
        pass

    def creaete_lv(self, volume_dic):
        """create logic volume for vpar
        :param: dict,include volume, name, path, ipaddress
        :returns: A list of up(running) vPar name
        """
        cmd_for_lvcreate = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': volume_dic['ip_addr'],
                'command': 'lvcreate -L '+ volume_dic['volume'] +
                           ' -n ' + volume_dic['volum_nm'] +
                           ' ' + volume_dic['path']
        }
        return utils.ExecRemoteCmd().exec_remote_cmd(
                **cmd_for_lvcreate)

    def define_vpar(self,vpar_dic):
        """create  vpar
        :param: dict,include vparname, memory size, path, ipaddress, CPU
                numbers
        :returns: A list of up(running) vPar name
        """
        cmd_for_vparcreate = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': volume_dic['ip_addr'],
                'command': 'vparcreate -p ' + vpar_dic['vpar_nm'] +
                           ' -a mem::' + vpar_dic['mem_size'] + '-a cpu::' +
                           vpar_dic['vcpu'] + ' -a disk:avio_stor::lv:' +
                           vpar_dic['path'] + '-a network:avio_lan::vswitch:' +
                           'sitelan' + ' -a network:avio_lan::vswitch:' +
                            'localnet'
        }
        return utils.ExecRemoteCmd().exec_remote_cmd(
                **cmd_for_vparcreate)

    def init_vpar(self, vpar_info):
        """Initialize the defined vpar so that could enter live console mode
        :param: A dict of vpar info including vpar_name and ip_addr
        :return: True if success as vpar run state turn into 'EFI'
        """
        cmd_for_vpar_init = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': vpar_info['ip_addr'],
                'command': '/opt/hpvm/bin/vparreset/vparboot -p ' +
                           vpar_info['vpar_name']
        }
        utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_vpar_init)
        # Sleep for a while to wait initialization completed.
        time.sleep(10)

        # Check RunState 'EFI' for whether it executed successfully
        cmd_for_init_check = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': vpar_info['ip_addr'],
                'command': '/opt/hpvm/bin/vparreset/vparstatus'
        }
        exec_result = utils.ExecRemoteCmd.exec_remote_cmd(**cmd_for_init_check)
        run_state = exec_result.strip().split('\n', 3)[2]
        if run_state is 'EFI':
            return True
        else:
            return False

    def get_mac_addr(self, ip_addr):
        """Get mac address of nPar site lan
        :param: string of npar ip_addr
        :returns: String of mac address
        """
        npar_name = self.get_instance_host_name(ip_addr)
        cmd_for_mac_addr = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': ip_addr,
                'command': '/opt/hpvm/bin/vparreset -p ' + npar_name + ' -v'
        }
        exec_result = utils.ExecRemoteCmd.exec_remote_cmd(**cmd_for_mac_addr)
        result = exec_result.strip().split('\n')
        for item in result:
            if 'sitelan' in item:
                mac_addr = item.strip().split(':')[2].split(',')[3]
        return mac_addr

    def register_vpar_into_ignite(self):
        pass
