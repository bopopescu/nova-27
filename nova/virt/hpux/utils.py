__author__ = 'psteam'

"""
A HP-UX Nova Compute driver.
"""

import pexpect

from nova import exception
from nova.openstack.common.gettextutils import _
from oslo.config import cfg

CONF = cfg.CONF


class ExecRemoteCmd(object):
    def exec_remote_cmd(self, **remote_cmd_info):
        execute_result = None
        try:
            ssh = pexpect.spawn('ssh %s@%s "%s"' %
                                (remote_cmd_info["username"],
                                 remote_cmd_info["ip_address"],
                                 remote_cmd_info["command"]))
            expect_ret = ssh.expect(['Password:',
                                     'continue connecting (yes/no)?'],
                                    timeout=CONF.hpux.ssh_timeout_seconds)
            if expect_ret == 0:
                ssh.sendline(remote_cmd_info["password"])
            elif expect_ret == 1:
                ssh.sendline("yes\n")
                ssh.expect("password:")
                ssh.sendline(remote_cmd_info["password"])
            else:
                raise exception.Invalid(_("ssh connection error UNKNOWN"))
            execute_result = ssh.read()
        except pexpect.EOF:
            raise exception.Invalid(_("pexpect error EOF"))
        except pexpect.TIMEOUT:
            raise exception.Invalid(_("pexpect error TIMEOUT"))
        except pexpect.ExceptionPexpect as e:
            raise exception.Invalid(_("pexpect error UNKNOWN"))
        finally:
            ssh.close()

        return execute_result

    def exec_efi_cmd(self, **efi_cmd_info):
        execute_result = None
        # It needs two interaction to execute efi shell command for,
        #   - 1) ssh to nPar to execute remote cmd 'vparconsole -p vpar_name'
        #   - 2) type 'CO' to enter efi console and execute efi shell command
        #        there
        # Have a try to have no password ssh connection and replace password
        # session with symbol 'CO', need real debug though!
        try:
            ssh = pexpect.spawn('ssh %s@%s "%s"' %
                                (efi_cmd_info["username"],
                                 efi_cmd_info["ip_address"],
                                 efi_cmd_info["remote_command"]))
            except_ret = ssh.expect([efi_cmd_info["vpar_name"]] + ' vMP>',
                                    timeout=CONF.hpux.ssh_timeout_seconds)
            if except_ret == 0:
                ssh.sendline('CO')
                ssh.expect("Shell>")
                ssh.sendline(efi_cmd_info["efi_command"])
            else:
                raise exception.Invalid(_("failed on efi shell connection"))
            execute_result = ssh.read()
        except pexpect.EOF:
            raise exception.Invalid(_("pexpect error EOF"))
        except pexpect.TIMEOUT:
            raise exception.Invalid(_("pexpect error TIMEOUT"))
        except pexpect.ExceptionPexpect as e:
            raise exception.Invalid(_("pexpect error UNKNOWN"))
        finally:
            ssh.close()
        return execute_result
