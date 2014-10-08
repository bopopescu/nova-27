__author__ = 'psteam'

"""
A HP-UX Nova Compute driver.
"""

import pexpect

class ExpectError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class RemoteCmdService(object):
    def exec_remote_cmd(self, **remote_cmd_info):
        # return "Hello World"

        execute_result = "Success"

        try:
            ssh = pexpect.spawn('ssh -l %s %s "%s"' %
                                (remote_cmd_info["username"],
                                remote_cmd_info["ip_address"],
                                remote_cmd_info["command"]
                                ))

            expect_ret = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=20)
            if expect_ret == 0:
                ssh.sendline(remote_cmd_info["password"])
            elif expect_ret == 1:
                ssh.sendline("yes\n")
                ssh.expect("password:")
                ssh.sendline(remote_cmd_info["password"])
            else:
                raise ExpectError("ssh expect unknown.")

            ssh.sendline(remote_cmd_info["command"])

            # res_remote_execute = ssh.read()

        except pexpect.EOF:
            execute_result = "pexpect EOF"
            #ssh.close()
        except pexpect.TIMEOUT:
            execute_result = "pexpect TIMEOUT"
            #ssh.close()
        except ExpectError:
            execute_result = "pexpect UNKNOWN"
        except:
            raise
        finally:
            ssh.close()

        return execute_result