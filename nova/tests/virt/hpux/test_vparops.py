__author__ = 'psteam'

import mock

from nova import test
from nova.virt.hpux import driver as hpux_driver
from nova.virt.hpux import hostops
from nova.virt.hpux import utils
from nova.virt.hpux import vparops
from oslo.config import cfg

CONF = cfg.CONF


class FakeInstance(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class VParOpsTestCase(test.TestCase):

    @mock.patch.object(utils.ExecRemoteCmd, 'exec_remote_cmd')
    @mock.patch.object(hostops.HostOps, '_get_client_list')
    def test_list_instances(self, mock_get_client_list, mock_exec_remote_cmd):
        up_state_vpar = 'vpar-test'
        npar_ip_addr = '192.168.169.100'
        vpar_names = [up_state_vpar]
        fake_npar_list = [{'ip_addr': npar_ip_addr,
                           'name': u'bl890npar1', 'hostname': u'bl890npar1',
                           'cpus': 8, 'memory': 66994944 / 1024,
                           'model': u'ia64 hp Integrity BL890c i4 nPar'}]
        fake_vpar_list = [{'name': 'vpar1', 'model': 'Virtual Partition',
                           'ip_addr': '192.168.0.11'}]
        mock_get_client_list.return_value = fake_npar_list, fake_vpar_list
        mock_exec_remote_cmd.return_value = ' \r\n[Virtual Partition]\r\n' +\
                        'Num Name  RunState State\r\n==' +\
                        '\r\n  2 ' + up_state_vpar + ' UP Active\r\n'
        cmd_for_npar = {
            'username': CONF.hpux.username,
            'password': CONF.hpux.password,
            'ip_address': npar_ip_addr,
            'command': '/opt/hpvm/bin/vparstatus'
        }
        conn = hpux_driver.HPUXDriver(None)
        result = conn.list_instances()
        self.assertEqual(vpar_names, result)
        mock_get_client_list.assert_called_once_with()
        mock_exec_remote_cmd.assert_called_once_with(**cmd_for_npar)

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

    @mock.patch.object(vparops.VParOps, 'update_dbprofile')
    def test_update_dbprofile(self, mock_update_dbprofile):
        fake_prof_update_info = {
            'vpar_name': 'vpar_one',
            'ip_address': '192.168.0.100',
            'prof_name': 'prof_test',
            'boot_fname': '/opt/ignite/boot/Rel_B.11.31/nbp.efi'
        }
        mock_update_dbprofile.return_value = True
        conn = hpux_driver.HPUXDriver(None)
        ret = conn._vparops.update_dbprofile(fake_prof_update_info)
        self.assertTrue(mock_update_dbprofile)
        mock_update_dbprofile.assert_called_once_with(fake_prof_update_info)
