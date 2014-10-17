__author__ = 'psteam'

"""
A HP-UX Nova Compute driver.
"""

from nova import db
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

        This method is called when nova-compute launches    , and
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

    def get_num_instances(self):
        """Get the current number of vpar

        Return integer with the number of running instances
        """
        instances_list = self.list_instances()
        return len(instances_list)

    def scheduler_dispatch(self, context, vPar_info):
        """Lookup target nPar.

        :param context:
        :param vPar_info: (dict) the required vPar info
        :returns: dictionary containing nPar info
        """
        nPar_list = db.npar_get_all(context)
        nPar = self._hostops.nPar_lookup(vPar_info, nPar_list)
        return nPar

    def instance_exists(self, instance_name):
        """Check target instance exists or not.

        :param instance_name:
        :return:
        :True:
        :False:
        """
        instance_list = self.list_instances()
        for inst_name in instance_list:
            if instance_name == inst_name:
                return True
            continue
        return False

    def get_instance_host_name(self, ip_addr):
        """Get the host (nPar) name of a given instance.

        Return string of nPar name
        """
        return self._vparops.get_instance_host_name(ip_addr)

    def destroy(self, context, instance, network_info, block_device_info=None,
                destroy_disks=True):
        """Destroy specific vpar

        :param context:
        :param instance:
        :param network_info:
        :param block_device_info:
        :param destroy_disks:
        :return:
        """
        if self.instance_exists(instance['display_name']):
            self._vparops.destroy(context, instance, network_info)

    def init_vpar(self, vpar_info):
        """Initialize the defined vPar.
        :param: A dict of vPar info including vPar name and ip address
        :return: True or False for whether it executes successfully
        """
        return self._vparops.init_vpar(vpar_info)

    def get_mac_addr(self, ip_addr):
        """Get mac address of nPar site lan
        :param: ip_addr:
        :return: mac address
        """
        return self._vparops.get_mac_addr(ip_addr)

    def spawn(self, context, instance, volume_dic, prof_define_info,
              vhba_info, prof_update_info, network_info=None):
        """Spawn new vapr

        :param context:
        :param instance:
        :param image_meta:
        :param injected_files:
        :param admin_password:
        :param network_info:
        :param block_device_info:
        :return:
        """
        self._vparops.spawn(context, instance, volume_dic, prof_define_info,
              vhba_info, prof_update_info, network_info=None)
