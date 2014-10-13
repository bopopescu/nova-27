__author__ = 'psteam'

import mock

from nova import test
from nova.virt.hpux import driver as hpux_driver
from nova.virt.hpux import vparops
from oslo.config import cfg

CONF = cfg.CONF


class VParOpsTestCase(test.TestCase):

    @mock.patch.object(vparops.VParOps, '_get_client_list')
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
