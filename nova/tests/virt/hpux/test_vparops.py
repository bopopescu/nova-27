__author__ = 'psteam'

import mock

from nova import test
from nova.virt.hpux import driver as hpux_driver
from nova.virt.hpux import hostops
from nova.virt.hpux import vparops


class FakeInstance(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class VParOpsTestCase(test.TestCase):

    @mock.patch.object(hostops.HostOps, '_get_client_list')
    def test_list_instances(self, mock_get_client_list):
        vpar_names = []
        fake_npar_list = [{'name': 'npar1', 'model': 'nPar',
                           'ip_addr': '192.168.0.10'}]
        fake_vpar_list = [{'name': 'vpar1', 'model': 'Virtual Partition',
                           'ip_addr': '192.168.0.11'}]
        mock_get_client_list.return_value = fake_npar_list, fake_vpar_list
        for vpar in fake_vpar_list:
            vpar_names.append(vpar['name'])
        conn = hpux_driver.HPUXDriver(None)
        result = conn.list_instances()
        self.assertEqual(vpar_names, result)
        mock_get_client_list.assert_called_once_with()

    @mock.patch.object(hpux_driver.HPUXDriver, 'instance_exists')
    def test_destroy(self, mock_instance_exists):
        fake_instance = FakeInstance()
        fake_instance = [{'nParname': 'npar1', 'vParname': 'vpar1',
                          'host': '10.10.0.1'}]
        ret_stat_beforedestroy = True
        if ret_stat_beforedestroy:
            vparops.VParOps().destroy(self, fake_instance, '10.10.0.1')
        conn = hpux_driver.HPUXDriver(None)
        mock_instance_exists.return_value = False
        ret_stat_afterdestroy = conn.instance_exists(fake_instance)
        print(ret_stat_afterdestroy)
        self.assertEqual(False, ret_stat_afterdestroy)
        self.assertNotEqual(ret_stat_beforedestroy, ret_stat_afterdestroy)
        mock_instance_exists.assert_called_once_with(fake_instance)

    @mock.patch.object(vparops.VParOps, 'define_dbprofile')
    def test_define_dbprofile(self, mock_define_dbprofile):
        fake_prof_define_info = {
            'vpar_name': 'vpar_one',
            'ip_address': '192.168.0.100',
            'cip': '192.168.0.101',
            'gip': '192.168.0.1',
            'mask': '255.255.255.0'
        }
        fake_prof_name = 'prof_test'
        mock_define_dbprofile.return_value = fake_prof_name
        conn = hpux_driver.HPUXDriver(None)
        ret = conn._vparops.define_dbprofile(fake_prof_define_info)
        self.assertEqual(fake_prof_name, ret)
        mock_define_dbprofile.assert_called_once_with(fake_prof_define_info)
