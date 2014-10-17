__author__ = 'psteam'

import mock

from nova import context
from nova import db
from nova import test
from nova.virt.hpux import driver as hpux_driver
from nova.virt.hpux import hostops
from nova.virt.hpux import vparops


class HPUXDriverTestCase(test.NoDBTestCase):
    """Unit tests for HP-UX driver calls."""

    @mock.patch.object(vparops.VParOps, 'list_instances')
    def test_list_instances(self, mock_list_instances):
        fake_instances = ['fake1', 'fake2']
        mock_list_instances.return_value = fake_instances
        conn = hpux_driver.HPUXDriver(None, vparops=vparops.VParOps())
        instances = conn.list_instances()
        self.assertEqual(fake_instances, instances)
        mock_list_instances.assert_called_once_with()

    @mock.patch.object(hostops.HostOps, 'get_host_stats')
    def test_get_host_stats(self, mock_get_host_stats):
        fake_stats = {
            'supported_instances': [],
            'vcpus': 2,
            'memory_mb': 2048,
            'local_gb': 100,
            'vcpus_used': 0,
            'memory_mb_used': 1024,
            'local_gb_used': 10,
            'hypervisor_type': 'hpux',
            'hypervisor_version': '201409',
            'hypervisor_hostname': 'hpux'
        }
        mock_get_host_stats.return_value = fake_stats
        conn = hpux_driver.HPUXDriver(None, hostops=hostops.HostOps())
        host_stats = conn.get_host_stats(refresh=True)
        self.assertEqual(fake_stats, host_stats)
        mock_get_host_stats.assert_called_once_with(refresh=True)

    @mock.patch.object(hostops.HostOps, 'get_available_resource')
    def test_get_available_resource(self, mock_get_available_resource):
        fake_resource = {
            'supported_instances': [],
            'vcpus': 2,
            'memory_mb': 2048,
            'local_gb': 100,
            'vcpus_used': 0,
            'memory_mb_used': 1024,
            'local_gb_used': 10,
            'hypervisor_type': 'hpux',
            'hypervisor_version': '201409',
            'hypervisor_hostname': 'hpux'
        }
        mock_get_available_resource.return_value = fake_resource
        conn = hpux_driver.HPUXDriver(None, hostops=hostops.HostOps())
        available_resource = conn.get_available_resource(None)
        self.assertEqual(fake_resource, available_resource)
        mock_get_available_resource.assert_called_once_with()

    @mock.patch.object(vparops.VParOps, 'get_info')
    def test_get_info(self, mock_get_info):
        fake_info = {
            'state': 'power_state.RUNNING',
            'max_mem': 4096,
            'mem': 2048,
            'num_cpu': 2,
            'cpu_time': None
        }
        mock_get_info.return_value = fake_info
        conn = hpux_driver.HPUXDriver(None, vparops=vparops.VParOps())
        fake_instance = {
            'name': 'fake1',
            'ip_addr': '192.168.0.1'
        }
        instance_info = conn.get_info(fake_instance)
        self.assertEqual(fake_info, instance_info)
        mock_get_info.assert_called_once_with(fake_instance)

    @mock.patch.object(hostops.HostOps, "nPar_lookup")
    @mock.patch.object(db, 'npar_get_all')
    def test_scheduler_dispatch(self, mock_npar_get_all, mock_nPar_lookup):
        fake_context = context.get_admin_context()
        fake_vPar_info = {
            'mem': 1024,
            'num_cpu': 2,
            'disk': 5
        }
        fake_nPar = {
            'supported_instances': [],
            'vcpus': 2,
            'memory_mb': 2048,
            'local_gb': 100,
            'vcpus_used': 0,
            'memory_mb_used': 1024,
            'local_gb_used': 10,
            'hypervisor_type': 'hpux',
            'hypervisor_version': '201409',
            'hypervisor_hostname': 'hpux'
        }
        fake_nPar_list = []
        fake_nPar_list.append(fake_nPar)
        mock_npar_get_all.return_value = fake_nPar_list
        mock_nPar_lookup.return_value = fake_nPar
        conn = hpux_driver.HPUXDriver(None, hostops=hostops.HostOps())
        nPar = conn.scheduler_dispatch(fake_context, fake_vPar_info)
        self.assertEqual(fake_nPar, nPar)
        mock_npar_get_all.assert_called_once_with(fake_context)
        mock_nPar_lookup.assert_called_once_with(fake_vPar_info,
                                                 fake_nPar_list)

    @mock.patch.object(hpux_driver.HPUXDriver, 'list_instances')
    def test_instance_exists_or_not(self, mock_list_instances):
        fake_instances = ['fake1', 'fake2']
        mock_list_instances.return_value = fake_instances
        conn = hpux_driver.HPUXDriver(None)
        self.assertTrue(conn.instance_exists('fake1'))
        self.assertFalse(conn.instance_exists('fake3'))
        mock_list_instances.assert_any_call()
        assert 2 == mock_list_instances.call_count

    @mock.patch.object(vparops.VParOps, 'get_instance_host_name')
    def test_get_instance_host_name(self, mock_get_instance_host_name):
        fake_host_name = 'napr1'
        fake_instance = {
            'name': 'vpar1',
            'ip_addr': '192.168.0.1'
        }
        mock_get_instance_host_name.return_value = fake_host_name
        conn = hpux_driver.HPUXDriver(None, vparops=vparops.VParOps())
        host_name = conn.get_instance_host_name(fake_instance['ip_addr'])
        self.assertEqual(fake_host_name, host_name)
        mock_get_instance_host_name.assert_called_once_with(
                                                    fake_instance['ip_addr'])

    @mock.patch.object(hpux_driver.HPUXDriver, 'get_num_instances')
    @mock.patch.object(hpux_driver.HPUXDriver, 'list_instances')
    def test_get_num_instances(self, mock_list_instances,
                               mock_get_num_instances):
        fake_instances = ['fake1', 'fake2']
        mock_list_instances.return_value = fake_instances
        mock_get_num_instances.return_value = 2
        conn = hpux_driver.HPUXDriver(None)
        instances = conn.get_num_instances()
        self.assertEqual(len(fake_instances), instances)
        mock_get_num_instances.assert_called_once_with()

    @mock.patch.object(vparops.VParOps, 'destroy')
    @mock.patch.object(hpux_driver.HPUXDriver, 'instance_exists')
    def test_destroy(self, mock_instance_exists, mock_destroy):
        fake_context = context.get_admin_context()
        fake_instance = {'display_name': 'vpar-test'}
        fake_network_info = {
            'fixed_ip': '1.1.1.1',
            'floating_ip': '11.11.11.11'
        }
        mock_instance_exists.return_value = True
        conn = hpux_driver.HPUXDriver(None)
        conn.destroy(fake_context, fake_instance, fake_network_info)
        mock_instance_exists.assert_called_once_with(
                                             fake_instance['display_name'])
        mock_destroy.assert_called_once_with(fake_context,
                                             fake_instance, fake_network_info)

    @mock.patch.object(vparops.VParOps, 'spawn')
    def test_spawn(self, mock_spawn):
        fake_context = context.get_admin_context()
        fake_instance = {'display_name': 'vpar-test'}
        fake_volume_dic = {
            'volume': 10000,
            'volume_nm': 'volum_test',
            'path': '/dev/vg0'
        }
        fake_prof_define_info = {
            'vpar_name': 'vpar_one',
            'ip_address': '192.168.0.100',
            'cip': '192.168.0.101',
            'gip': '192.168.0.1',
            'mask': '255.255.255.0'
        }
        fake_prof_update_info = {
            'vpar_name': 'vpar_one',
            'ip_address': '192.168.0.100',
            'prof_name': 'prof_test',
            'boot_fname': '/opt/ignite/boot/Rel_B.11.31/nbp.efi'
        }
        fake_vhba_info = {
            'vpar_name': 'vpar_one',
            'vpar_component': 'test_unknown',
            'wwpn': 'pwwn',
            'wwnn': 'nwwn'
        }
        conn = hpux_driver.HPUXDriver(None)
        conn.spawn(fake_context, fake_instance, fake_volume_dic,
                   fake_prof_define_info, fake_vhba_info,
                   fake_prof_update_info, network_info=None)
        mock_spawn.assert_called_once_with(fake_context, fake_instance,
                                           fake_volume_dic,
                                           fake_prof_define_info,
                                           fake_vhba_info, fake_prof_update_info,
                                           network_info=None)

    @mock.patch.object(vparops.VParOps, 'get_mac_addr')
    def test_get_mac_addr(self, mock_get_mac_addr):
        fake_ip_addr = '192.168.0.1'
        fake_mac_addr = '0x123456'
        mock_get_mac_addr.return_value = fake_mac_addr
        conn = hpux_driver.HPUXDriver(None)
        mac_addr = conn.get_mac_addr(fake_ip_addr)
        self.assertEqual(fake_mac_addr, mac_addr)
        mock_get_mac_addr.assert_called_once_with(fake_ip_addr)

    @mock.patch.object(vparops.VParOps, 'init_vpar')
    def test_init_vpar(self, mock_init_vpar):
        fake_vpar_info = {
            'vpar_name': 'vpar_fake1',
            'ip_addr': '192.168.0.1'
        }
        mock_init_vpar.return_value = True
        conn = hpux_driver.HPUXDriver(None)
        exec_result = conn.init_vpar(fake_vpar_info)
        self.assertTrue(exec_result)
        mock_init_vpar.assert_called_once_with(fake_vpar_info)
