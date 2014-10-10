__author__ = 'psteam'

"""
Management class for host operations.
"""

from nova.openstack.common.gettextutils import _
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class HostOps(object):
    def __init__(self):
        self._stats = None

    def _get_vcpu_total(self):
        """Get available vcpu number of physical computer.

        :returns: the number of cpu core instances can be used.

        """
        return 2

    def _get_vcpu_used(self):
        """Get vcpu usage number of physical computer.

        :returns: The total number of vcpu(s) that are currently being used.

        """
        return 1

    def _get_memory_mb_total(self):
        """Get the total memory size(MB) of physical computer.

        :returns: the total amount of memory(MB).

        """

        return 2048

    def _get_memory_mb_used(self):
        """Get the free memory size(MB) of physical computer.

        :returns: the total usage of memory(MB).

        """
        return 1024

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

        disk_info_dict = self._get_local_gb_info()
        data = {}
        data['supported_instances'] = []

        data['vcpus'] = self._get_vcpu_total()
        data['memory_mb'] = self._get_memory_mb_total()
        data['local_gb'] = disk_info_dict['total']
        data['vcpus_used'] = self._get_vcpu_used()
        data['memory_mb_used'] = self._get_memory_mb_used()
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
