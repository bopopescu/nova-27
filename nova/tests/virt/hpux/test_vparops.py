__author__ = 'psteam'

import mock

from nova import context
from nova import db
from nova import test
from nova.virt.hpux import driver as hpux_driver
from nova.virt.hpux import utils
from oslo.config import cfg

CONF = cfg.CONF


class VParOpsTestCase(test.TestCase):

    @mock.patch.object(utils.ExecRemoteCmd, 'exec_remote_cmd')
    @mock.patch.object(db, 'npar_get_all')
    @mock.patch.object(context, 'get_admin_context')
    def test_list_instances(self, mock_get_admin_context,
                            mock_npar_get_all, mock_exec_remote_cmd):
        fake_context = {'project_id': None, 'user_id': None,
                        '_read_deleted': 'no', 'auth_token': None,
                        'is_admin': True, 'service_catalog': []}
        up_state_vpar = 'vpar-test'
        npar_ip_addr = '192.168.169.100'
        vpar_names = [up_state_vpar]
        fake_npar_list = [{'ip_addr': npar_ip_addr,
                           'name': u'bl890npar1', 'hostname': u'bl890npar1',
                           'cpus': 8, 'memory': 66994944 / 1024,
                           'model': u'ia64 hp Integrity BL890c i4 nPar'}]
        mock_get_admin_context.return_value = fake_context
        mock_npar_get_all.return_value = fake_npar_list
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
        mock_get_admin_context.assert_called_once_with()
        mock_npar_get_all.assert_called_once_with(fake_context)
        mock_exec_remote_cmd.assert_called_once_with(**cmd_for_npar)
