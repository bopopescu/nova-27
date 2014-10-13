__author__ = 'psteam'

"""
Management class for basic vPar operations.
"""

from xml.dom import minidom

from nova.virt.hpux import utils
from oslo.config import cfg

hpux_opts = [
    cfg.StrOpt('username',
               default='root',
               help='username for ssh command'),
    cfg.StrOpt('password',
               default='root',
               help='password for ssh command'),
    cfg.StrOpt('ignite_ip',
               default='192.168.172.52',
               help='IP for ignite server'),
    ]
CONF = cfg.CONF
CONF.register_opts(hpux_opts, 'hpux')


class VParOps(object):

    def __init__(self):
        pass

    def _get_client_list(self):
        """Get client (npar/vpar) list."""
        npar_list = []
        vpar_list = []
        cmd_for_ignite = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': CONF.hpux.ignite_ip,
            'command': '/opt/ignite/bin/ignite client list -m xml -l details'
        }
        exec_result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_ignite)
        dom1 = minidom.parseString(exec_result)
        clients_xml = dom1.getElementsByTagName("iux:client")
        for item in clients_xml:
            client_dict = {'name': '', 'model': '', 'ip_addr': ''}
            client_dict['name'] = item.getAttribute('name')
            attr_list = item.getElementsByTagName('iux:attr')
            for attr in attr_list:
                if attr.getAttribute('name') == 'model':
                    client_dict['model'] = attr.childNodes[0].nodeValue
                elif attr.getAttribute('name') == 'ipaddress':
                    client_dict['ip_addr'] = attr.firstChild.nodeValue
                else:
                    continue
            if 'nPar' in client_dict['model']:
                npar_list.append(client_dict)
            if 'Virtual Partition' in client_dict['model']:
                vpar_list.append(client_dict)
        return npar_list, vpar_list

    def list_instances(self):
        vpar_names = []
        npar_list, vpar_list = self._get_client_list()
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
