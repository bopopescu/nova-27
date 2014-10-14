__author__ = 'psteam'

"""
Management class for host operations.
"""

from nova import context
from nova import db
from nova.openstack.common.gettextutils import _
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging
from nova.virt.hpux import utils
from oslo.config import cfg
from xml.dom import minidom

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

LOG = logging.getLogger(__name__)


class HostOps(object):
    def __init__(self):
        self._stats = None

    def _get_cpu_and_memory_mb_free(self, ip_addr):
        """Get the free cpu core and memory size(MB) of nPar.

        :param ip_addr: IP address of specified nPar
        :returns: A dict containing:
             :cpus_free: How much cpu is free
             :memory_free: How much space is free (in MB)
        """
        info = {'cpus_free': 0, 'memory_free': 0}
        cmd_for_npar = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': ip_addr,
            'command': '/opt/hpvm/bin/vparstatus -A'
        }
        exec_result = utils.ExecRemoteCmd().exec_remote_cmd(**cmd_for_npar)
        results = exec_result.strip().split('\n')
        for item in results:
            if 'Available CPUs' in item:
                # item likes '[Available CPUs]:  5\r'
                info['cpus_free'] = item.split(':')[1].strip()
            elif 'Available Memory' in item:
                # item likes '[Available Memory]:  55936 Mbytes\r'
                info['memory_free'] = item.split(':')[1].split()[0].strip()
            else:
                continue
        return info

    def _get_local_gb_info(self):
        """Get local storage info of the compute node in GB.

        :returns: A dict containing:
             :total: How big the overall usable filesystem is (in gigabytes)
             :free: How much space is free (in gigabytes)
             :used: How much space is used (in gigabytes)
        """
        info = {}
        info['total'] = 100
        info['free'] = 80
        info['used'] = 20

        return info

    def _get_hypervisor_type(self):
        """Get hypervisor type.

        :returns: hypervisor type (ex. qemu)

        """
        return 'hpux'

    def _get_hypervisor_version(self):
        """Get hypervisor version.

        :returns: hypervisor version (ex. 12003)

        """
        return '20140918'

    def _get_hypervisor_hostname(self):
        """Returns the hostname of the hypervisor."""
        return 'hpux'

    def _get_cpu_info(self):
        """Get cpuinfo information.

        Obtains cpu feature from virConnect.getCapabilities,
        and returns as a json string.

        :return: see above description

        """
        cpu_info = dict()

        return jsonutils.dumps(cpu_info)

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
                elif attr.getAttribute('name') == 'hostname':
                    client_dict['hostname'] = attr.firstChild.nodeValue
                elif attr.getAttribute('name') == 'memory':
                    client_dict['memory_total'] = attr.firstChild.nodeValue
                elif attr.getAttribute('name') == 'cpus':
                    client_dict['cpus_total'] = attr.firstChild.nodeValue
                else:
                    continue
            if 'nPar' in client_dict['model']:
                npar_list.append(client_dict)
            if 'Virtual Partition' in client_dict['model']:
                vpar_list.append(client_dict)
        return npar_list, vpar_list

    def get_host_stats(self, refresh=False):
        """Return the current state of the host.

        If 'refresh' is True, run update the stats first.
        """
        if refresh or not self._stats:
            self._update_status()
        return self._stats

    def get_available_resource(self):
        """Retrieve resource info.

        This method is called when nova-compute launches, and
        as part of a periodic task.

        :returns: dictionary describing resources

        """
        LOG.debug(_('get_available_resource called'))
        stats = self.get_host_stats(refresh=True)
        stats['supported_instances'] = jsonutils.dumps(
                stats['supported_instances'])
        return stats

    def _update_status(self):
        LOG.debug(_("Updating host stats"))

        data = {}
        data['supported_instances'] = []

        admin_context = context.get_admin_context()
        npar_list, vpar_list = self._get_client_list()
        for npar in npar_list:
            update_info = {}
            cpu_mem_dict = self._get_cpu_and_memory_mb_free(npar['ip_addr'])
            update_info['vcpus_used'] = (npar['cpus_total'] -
                                         cpu_mem_dict['cpus_free'])
            update_info['memory_used'] = (npar['memory_total'] -
                                             cpu_mem_dict['memory_free'])
            update_info['vcpus'] = npar['cpus_total']
            update_info['memory'] = npar['memory_total']
            # Try to create/update npar info into table "nPar_resource"
            npar_resource = db.npar_get_by_ip(admin_context, npar['ip_addr'])
            if npar_resource:
                db.npar_resource_update(admin_context,
                                        npar['ip_addr'], update_info)
            else:
                update_info['ip_addr'] = npar['ip_addr']
                db.npar_resource_create(admin_context, update_info)
            # Sum up all the nPar resources
            data['vcpus'] += npar['cpus_total']
            data['memory_mb'] += npar['memory_total']
            data['vcpus_used'] += update_info['vcpus_used']
            data['memory_mb_used'] += update_info['memory_used']

        # Here, disk info is still fake data.
        disk_info_dict = self._get_local_gb_info()
        data['local_gb'] = disk_info_dict['total']
        data['local_gb_used'] = disk_info_dict['used']
        data['hypervisor_type'] = self._get_hypervisor_type()
        data['hypervisor_version'] = self._get_hypervisor_version()
        data['hypervisor_hostname'] = self._get_hypervisor_hostname()
        data['cpu_info'] = self._get_cpu_info()
        self._stats = data

        return data

    def nPar_lookup(self, vPar_info, nPar_list):
        # Initial dispatch policy
        for nPar in nPar_list:
            current_mem = nPar['memory_mb'] - nPar['memory_mb_used']
            current_vcpus = nPar['vcpus'] - nPar['vcpus_used']
            current_disk = nPar['local_gb'] - nPar['local_gb_used']
            if (vPar_info['mem'] < current_mem and
                vPar_info['num_cpu'] < current_vcpus and
                vPar_info['disk'] < current_disk):
                return nPar
        return None

    def nPar_resource(self, nPar_info):
        """Deal with nPar resource data
        """
        npar_stats_total = {
            'vcpus': 0,
            'memory_mb': 0,
            'local_gb': 0
        }
        npar_stats_total['vcpus'] += nPar_info['vcpus']
        npar_stats_total['memory_mb'] += nPar_info['memory_mb']
        npar_stats_total['local_gb'] += nPar_info['local_gb']
        return npar_stats_total
