__author__ = 'psteam'

"""
A HP-UX Nova Compute driver.
"""

from nova.virt import driver
from nova.virt.hpux import hostops
from nova.virt.hpux import vparops


class HPUXDriver(driver.ComputeDriver):
    def __init__(self, virtapi,
                 vparops=vparops.VParOps(),
                 hostops=hostops.HostOps()):
        super(HPUXDriver, self).__init__(virtapi)
        self._vparops = vparops
        self._hostops = hostops

    def init_host(self, host):
        pass

    def list_instances(self):
        return self._vparops.list_instances()

    def get_host_stats(self, refresh=False):
        """Return the current state of the host.

        If 'refresh' is True, run update the stats first.
        """
        return self._hostops.get_host_stats(refresh=refresh)

    def get_available_resource(self, nodename):
        """Retrieve resource information.

        This method is called when nova-compute launches, and
        as part of a periodic task that records the results in the DB.

        :param nodename: will be put in PCI device
        :returns: dictionary containing resource info
        """
        return self._hostops.get_available_resource()

    def get_info(self, instance):
        """Get the current status of an instance, by name (not ID!)

        :param instance: nova.objects.instance.Instance object

        Returns a dict containing:

        :state:           the running state, one of the power_state codes
        :max_mem:         (int) the maximum memory in KBytes allowed
        :mem:             (int) the memory in KBytes used by the domain
        :num_cpu:         (int) the number of virtual CPUs for the domain
        :cpu_time:        (int) the CPU time used in nanoseconds
        """
        return self._vparops.get_info(instance)
