__author__ = 'psteam'

from nova import test
from nova.virt.hpux import utils


class ExecRemoteCmdTestCase(test.TestCase):

    @test.testtools.skip("exec_remote_cmd")
    def test_exec_remote_cmd(self):
        remote_cmd_info = {
            "username": "psteam",
            "password": "hpinvent",
            "ip_address": "127.0.0.1",
            "command": "echo 'Hello World'"
        }
        remote_cmd = utils.ExecRemoteCmd()
        ret_str = remote_cmd.exec_remote_cmd(**remote_cmd_info)
        self.assertEqual("Hello World", ret_str.strip())
