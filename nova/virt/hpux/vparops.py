__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""

import pxssh
import re

from nova import context
from nova import db
from nova import exception
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.virt.hpux import hostops
from nova.virt.hpux import utils
from oslo.config import cfg

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class VParOps(object):

    def __init__(self):
        pass

    def _get_vpar_resource_info(self, vpar_name, npar_ip_addr):
        """Get vPar resource info.

        :returns: A dict including CPU, memory and run state info.
        """
        vpar_info = {}
        cmd_for_vpar = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': npar_ip_addr,
            'command': '/opt/hpvm/bin/vparstatus -p ' + vpar_name + ' -v'
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

        admin_context = context.get_admin_context()
        npar_list = db.npar_get_all(admin_context)

        for npar in npar_list:
            cmd_for_npar = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': npar['ip_addr'],
                'command': '/opt/hpvm/bin/vparstatus'
            }
            exec_result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_npar)
            results = exec_result.strip().split('\n')
            for ret in results:
                # ret likes '  2 vpar-test  UP  Active \r'
                if 'UP' in ret:
                    vpar_names.append(ret.split()[1])
        return vpar_names

    def get_info(self, instance):
        """Get status of given vPar instance.

        :returns: A dict including CPU, memory, disk info and
        run state of required vPar.
        """
        # TODO(Lei Li): This will be replaced since nPar_list
        # will get by reading from DB directly. Cut such code for now.
        #napr_list, vpar_list = hostops.HostOps()._get_client_list()
        #for vpar in vpar_list:
            #if vpar['name'] is instance['name']:
        vpar_info = self._get_vpar_resource_info(instance['vpar_name'],
                                                 instance['npar_ip_addr'])
        if not vpar_info:
            raise exception.VparNotFound(instance['name'])
        else:
            return vpar_info

    def destroy(self, context, instance, network_info):
        """Destroy vPar on specified nPar.

        :param instance:
        :returns:
        """
        LOG.debug(_("Begin to destroy vPar %s.") % instance['display_name'])
        # Power off vpar before "vparremove"
        cmd = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': instance['host'],
            'command': '/opt/hpvm/bin/vparreset -p '
                       + instance['display_name'] + ' -d -f'
        }
        utils.ExecRemoteCmd().exec_remote_cmd(**cmd)
        # Get specified vPar info
        vpar_info = self._get_vpar_resource_info(instance['display_name'],
                                                 instance['host'])
        # Delete the specified vPar if status is "DOWN"
        if vpar_info['run_state'] == 'DOWN':
            cmd = {
                'username': CONF.hpux.username,
                'password': CONF.hpux.password,
                'ip_address': instance['host'],
                'command': '/opt/hpvm/bin/vparremove -p '
                           + instance['display_name'] + ' -f'
            }
            utils.ExecRemoteCmd().exec_remote_cmd(**cmd)
            LOG.debug(_("Destroy vPar %s successfully.")
                      % instance['display_name'])

    def create_lv(self, lv_dic):
        """Create logical volume for vPar on specified nPar.

        :param: A dict containing:
             :lv_size: The size of logical volume
             :lv_name: The name of logical volume
             :vg_path: The path of volume group
             :host: The IP address of specified nPar
        :returns: created_lv_path: The path of created logical volume
        """
        cmd = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': lv_dic['host'],
            'command': 'lvcreate -L ' + lv_dic['lv_size'] +
                       ' -n ' + lv_dic['lv_name'] +
                       ' ' + lv_dic['vg_path']
        }
        created_lv_path = lv_dic['vg_path'] + '/r' + lv_dic['lv_name']
        LOG.debug(_("Begin to create logical volume %s.")
                  % lv_dic['lv_name'])
        result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd)
        if created_lv_path in result:
            LOG.debug(_("Create logical volume %s successfully.")
                      % created_lv_path)
            return created_lv_path
        return None

    def define_vpar(self, vpar_dic):
        """Define vPar resources on specified nPar.

        :param: A dict containing:
             :vpar_name: The name of vPar
             :host: The IP address of specified nPar
             :mem: The memory of vPar
             :cpu: The cpu of vPar
             :lv_path: The path of logical volume
        :returns:
        """
        cmd = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': vpar_dic['host'],
            'command': '/opt/hpvm/bin/vparcreate -p ' +
                       vpar_dic['vpar_name'] +
                       ' -a mem::' + str(vpar_dic['mem']) +
                       ' -a cpu::' + str(vpar_dic['cpu']) +
                       ' -a disk:avio_stor::lv:' + vpar_dic['lv_path'] +
                       ' -a network:avio_lan::vswitch:' +
                       CONF.hpux.management_network +
                       ' -a network:avio_lan::vswitch:' +
                       CONF.hpux.production_network
        }
        utils.ExecRemoteCmd().exec_remote_cmd(**cmd)

    def init_vpar(self, vpar_info):
        """Initialize the specified vPar so that could enter live console mode.

        :param: A dict containing:
             :vpar_name: The name of vPar
             :host: The IP address of specified nPar
        :return: True if vPar boot successfully
        """
        cmd = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': vpar_info['host'],
            'command': '/opt/hpvm/bin/vparboot -p ' +
                       vpar_info['vpar_name']
        }
        LOG.debug(_("Begin to initialize vPar %s.") % vpar_info['vpar_name'])
        result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd)
        if 'Successful start initiation' in result:
            LOG.debug(_("Initialize vPar %s successfully.")
                      % vpar_info['vpar_name'])
            return True
        return False

    def get_mac_addr(self, vpar_info):
        """Get "sitelan" MAC address of vPar from specified nPar.

        :param: A dict containing:
             :vpar_name: The name of vPar
             :host: The IP address of specified nPar
        :return: mac_addr: The MAC address of vPar
        """
        mac_addr = None
        cmd = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': vpar_info['host'],
            'command': '/opt/hpvm/bin/vparstatus -p ' +
                       vpar_info['vpar_name'] + ' -v'
        }
        exec_result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd)
        results = exec_result.strip().split('\n')
        for item in results:
            if CONF.hpux.management_network in item:
                io_details = item.split()
                for io in io_details:
                    if CONF.hpux.management_network in io:
                        mac_addr = io.split(':')[2].split(',')[2]
        return mac_addr

    def register_vpar_into_ignite(self, vpar_info):
        """Register vPar into ignite server.

        :param: A dict containing:
             :vpar_name: The name of vPar
             :mac: The mac address of vPar
             :ip_addr: The IP address of vPar
             :gateway: The gateway of vPar
             :mask: The mask of vPar
        :return: True if no error in the process of registration
        """
        # Add vPar network info into the end of /etc/bootptab on ignite server
        cmd_for_network = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': CONF.hpux.ignite_ip,
            'command': ' echo \'' + vpar_info['vpar_name'] + ':\\\''
                + ' >> /etc/bootptab'
                + ' && echo \'\ttc=ignite-defaults:\\\'' + ' >> /etc/bootptab'
                + ' && echo \'\tha=' + vpar_info['mac'] + ':\\\''
                + ' >> /etc/bootptab'
                + ' && echo \'\tbf=/opt/ignite/boot/Rel_B.11.31/nbp.efi:\\\''
                + ' >> /etc/bootptab'
                + ' && echo \'\tgw=' + vpar_info['gateway'] + ':\\\''
                + ' >> /etc/bootptab'
                + ' && echo \'\tip=' + vpar_info['ip_addr'] + ':\\\''
                + ' >> /etc/bootptab'
                + ' && echo \'\tsm=' + vpar_info['mask'] + '\''
                + ' >> /etc/bootptab'
        }
        utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_network)

        # Create config file for client(vPar)
        cmd_for_create_config = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': CONF.hpux.ignite_ip,
            'command': 'mkdir /var/opt/ignite/clients/' + vpar_info['mac'] +
                       '&& touch /var/opt/ignite/clients/' + vpar_info['mac'] +
                       '/config'
        }
        utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_create_config)

        # Add config info into the end of /var/opt/ignite/clients/<MAC>/config
        cmd_for_config = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': CONF.hpux.ignite_ip,
            'command': ' echo \'cfg "HP-UX B.11.31.1403 golden_image"=TRUE\''
                + '>> /var/opt/ignite/clients/' + vpar_info['mac'] + '/config'
                + ' && echo \'_hp_cfg_detail_level="v"\''
                + '>> /var/opt/ignite/clients/' + vpar_info['mac'] + '/config'
                + ' && echo \'final system_name="' + vpar_info['vpar_name']
                + '"\'' + '>> /var/opt/ignite/clients/' + vpar_info['mac']
                + '/config'
                + ' && echo \'_hp_keyboard="USB_PS2_DIN_US_English"\''
                + '>> /var/opt/ignite/clients/' + vpar_info['mac'] + '/config'
                + ' && echo \'root_password="1uGsgzGKG95gU"\''
                + '>> /var/opt/ignite/clients/' + vpar_info['mac'] + '/config'
                + ' && echo \'_hp_root_disk="0/0/0/0.0x0.0x0"\''
                + '>> /var/opt/ignite/clients/' + vpar_info['mac'] + '/config'
                + ' && echo \'_my_second_disk_path=""\''
                + '>> /var/opt/ignite/clients/' + vpar_info['mac'] + '/config'
        }
        utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_config)
        return True

    def lanboot_vpar_by_efi(self, vpar_info):
        """Lanboot vPar by enter EFI Shell on specified nPar.

        :param: A dict containing:
             :vpar_name: The name of vPar
             :host: The IP address of specified nPar
             :ip_addr: The IP address of vPar
             :gateway: The gateway of vPar
             :mask: The mask of vPar
        :return: True if no error in the process of lanboot
        """
        cmd_vparconsole = '/opt/hpvm/bin/vparconsole -P '\
                          + vpar_info['vpar_name']
        cmd_dbprofile_network = 'dbprofile -dn profile-test' +\
                                ' -sip ' + CONF.hpux.ignite_ip +\
                                ' -cip ' + vpar_info['ip_addr'] +\
                                ' -gip ' + vpar_info['gateway'] +\
                                ' -m ' + vpar_info['mask']
        cmd_dbprofile_kernel = 'dbprofile -dn profile-test' +\
                               ' -b "/opt/ignite/boot/Rel_B.11.31/nbp.efi"'
        cmd_lanboot = 'lanboot select -index 01 -dn profile-test'
        try:
            LOG.debug(_("Begin to lanboot vPar %s by enter EFI Shell.")
                      % vpar_info['vpar_name'])
            # Get ssh connection
            ssh = pxssh.pxssh()
            ssh.login(vpar_info['host'], CONF.hpux.username,
                      CONF.hpux.password, original_prompt='[$#>]',
                      login_timeout=CONF.hpux.ssh_timeout_seconds)

            # Send command "vparconsole -P <vpar_name>"
            ssh.sendline(cmd_vparconsole)
            ssh.prompt(timeout=CONF.hpux.ssh_timeout_seconds)
            ssh.sendline('CO')
            ssh.sendline('\r\n')
            ssh.prompt(timeout=CONF.hpux.ssh_timeout_seconds)
            # Replace the color code of output
            efi_prompt = re.sub('\x1b\[[0-9;]*[m|H|J]', '', ssh.before)
            efi_prompt = re.sub('\[0m', '', efi_prompt)

            # Send "Ctrl-Ecf" to EFI Shell if have no write access
            if 'Read only' in efi_prompt[-70:]:
                # [Read only - use Ctrl-Ecf for console write access.]
                ssh.send('\x05\x63\x66')
                ssh.sendline('\r\n')
                ssh.prompt(timeout=CONF.hpux.ssh_timeout_seconds)

            # Send command related to "dbprofile"
            ssh.sendline(cmd_dbprofile_network)
            ssh.sendline('\r\n')
            ssh.prompt(timeout=CONF.hpux.ssh_timeout_seconds)
            ssh.sendline(cmd_dbprofile_kernel)
            ssh.sendline('\r\n')
            ssh.prompt(timeout=CONF.hpux.ssh_timeout_seconds)
            # Output the log before executing "lanboot"
            console_log = re.sub('\x1b\[[0-9;]*[m|H|J]', '', ssh.before)
            LOG.info(_("\n%s") % console_log)

            # Send command related to "lanboot"
            ssh.send(cmd_lanboot)
            ssh.send('\r\n')
            ssh.prompt(timeout=CONF.hpux.lanboot_timeout_seconds)
        except pxssh.ExceptionPxssh:
            raise exception.Invalid(_("pxssh failed on login."))
        finally:
            ssh.logout()

        return True

    def init_vhba(self, vhba_info):
        #Attach vhba
        cmd_for_vhba = {
            'username': 'root',
            'password': 'root',
            'ip_address': vhba_info['host'],
            'command': 'vparreset -f -p ' + vhba_info['vpar_name'] + ' -d'
        }
        utils.ExecRemoteCmd.exec_remote_cmd(**cmd_for_vhba)
        #Force to reset vPar, must succeed:
        cmd_for_vhba = {
            'username': 'root',
            'password': 'root',
            'ip_address': vhba_info['host'],
            'command': 'vparmodify -p ' + vhba_info['vpar_name'] + ' -a ' +
                       vhba_info['vpar_component'] + ':avio_stor:,,' +
                       vhba_info['wwpn'] + ',' + vhba_info['wwnn'] +
                       ':npiv:/dev/fcd0'
        }
        utils.ExecRemoteCmd.exec_remote_cmd(**cmd_for_vhba)
        return True

    def boot_vpar(self, vpar_info):
        cmd_for_boot = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': vpar_info['host'],
            'command': 'vparboot -p ' + vpar_info['vpar_name']
        }
        return utils.ExecRemoteCmd.exec_remote_cmd(**cmd_for_boot)
