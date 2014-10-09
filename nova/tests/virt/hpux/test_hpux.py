__author__ = 'psteam'

import mock

from nova import context
from nova import db
from nova import test
from nova.virt.hpux import driver as hpux_driver
from nova.virt.hpux import hostops
from nova.virt.hpux import utils
from nova.virt.hpux import vparops


class FakeInstance(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


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
            'name': 'fake1'
        }
        instance_info = conn.get_info(fake_instance)
        self.assertEqual(fake_info, instance_info)
        mock_get_info.assert_called_once_with(fake_instance)

    #@test.testtools.skip("exec_remote_cmd")
    def test_exec_remote_cmd(self):
        remote_cmd_info = {
            "username": "psteam",
            "password": "hpinvent",
            "ip_address": "127.0.0.1",
            "command": "echo 'Hello World'"
        }

        remote_cmd = utils.ExecRemoteCmd()
        ret_str = remote_cmd.exec_remote_cmd(**remote_cmd_info)

        self.assertEqual("Hello World", ret_str)

    @mock.patch.object(hostops.HostOps, "nPar_lookup")
    @mock.patch.object(db, 'nPar_get_all')
    def test_scheduler_dispatch(self, mock_nPar_get_all, mock_nPar_lookup):
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
        mock_nPar_get_all.return_value = fake_nPar_list
        mock_nPar_lookup.return_value = fake_nPar
        conn = hpux_driver.HPUXDriver(None, hostops=hostops.HostOps())
        nPar = conn.scheduler_dispatch(fake_vPar_info)
        self.assertEqual(fake_nPar, nPar)
        mock_nPar_get_all.assert_called_once_with()
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

    @mock.patch.object(hpux_driver.HPUXDriver, 'list_instances')
    def test_get_num_instances(self, mock_list_instances):
        fake_instances = ['fake1', 'fake2']
        mock_list_instances.return_value = fake_instances
        conn = hpux_driver.HPUXDriver(None)
        self.assertEqual(2, conn.get_num_instances())
        mock_list_instances.assert_called_once_with()

    @mock.patch.object(vparops.VParOps, 'destroy')
    def test_destroy(self, mock_destroy):
        fake_context = context.get_admin_context()
        fake_instance = FakeInstance()
        fake_network_info = {
            'fixed_ip': '1.1.1.1',
            'floating_ip': '11.11.11.11'
        }
        conn = hpux_driver.HPUXDriver(None)
        conn.destroy(fake_context, fake_instance, fake_network_info)
        mock_destroy.assert_called_once_with(fake_context,
                                             fake_instance, fake_network_info)

    @mock.patch.object(vparops.VParOps, 'spawn')
    def test_spawn(self, mock_spawn):
        fake_context = context.get_admin_context()
        fake_instance = FakeInstance()
        fake_image_meta = {
            'image_id': '111111111111111',
            'image_name': 'fake_image_name_1'
        }
        fake_injected_files = None
        fake_admin_password = 'fake_password'
        conn = hpux_driver.HPUXDriver(None)
        conn.spawn(fake_context, fake_instance, fake_image_meta,
                   fake_injected_files, fake_admin_password,
                   network_info=None, block_device_info=None)
        mock_spawn.assert_called_once_with(fake_context, fake_instance,
                                       fake_image_meta, fake_injected_files,
                                       fake_admin_password, network_info=None,
                                       block_device_info=None)
