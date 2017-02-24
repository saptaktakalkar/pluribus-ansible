#!/usr/bin/python
""" PN module for auto SSH key setup """

# Copyright 2016 Pluribus Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import subprocess
import paramiko
import shlex

DOCUMENTATION = """
---
module: pn_autossh
author: "Pluribus Networks"
version: 1.0
short_description: Module to auto setup SSH keys between localhost and remote nodes.
description:
  - This module checks for SSH keys on localhost and generates them if they don't exist.
    The public key of the localhost is then pushed to the remote nodes for password-less
    authentication.
options:
  pn_user:
    description:
      - Provide remote user name.
    required: True
    type: str
  pn_ssh_password:
    description:
      - Provide SSH login password.
    required: True
    type: str
  pn_hosts_csv:
     description:
       - Provide topology information in a csv file in (hostname, ip) format.
     required: True
     type: str
  pn_overwrite:
     description:
       - Flag that inform if /.ssh/authorized_keys file should be overwritten or appended.
     required: False
     type: bool
     default: False
  pn_filepath:
     description:
       - File path to save the keys on localhost.
     required: True
     type: str
"""

EXAMPLES = """

"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vlan command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vlan command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""



def deploy_key(sshkey, address, username, password, overwrite):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(address, username=username, password=password)
    client.exec_command('mkdir -p ~/.ssh/')
    if overwrite is True:
        client.exec_command('echo "%s" > ~/.ssh/authorized_keys' % sshkey)
    else:
        client.exec_command('echo "%s" >> ~/.ssh/authorized_keys' % sshkey)
    client.exec_command('chmod 644 ~/.ssh/authorized_keys')
    client.exec_command('chmod 700 ~/.ssh/')
    return "Keys Pushed to host: %s \n" % address


def generate_key(path):
    cmd = 'ssh-keygen -t rsa -f %s -q -N %s' % (path, '""')
    cmd = shlex.split(cmd)
    response = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()
    if out:
        return out
    if err:
        return err
    else:
        return 'SSH Keys generated on localhost \n'


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_user=dict(required=False, type='str'),
            pn_ssh_password=dict(required=False, type='str'),
            pn_hosts_csv=dict(required=True, type='str'),
            pn_overwrite=dict(required=False, type='bool', default=False),
            pn_filepath=dict(required=True, type='str')
        )
    )
    message = ''
    user = module.params['pn_user']
    ssh_password = module.params['pn_ssh_password']
    csv_data = module.params['pn_hosts_csv']
    filepath = module.params['pn_filepath']
    overwrite = module.params['pn_overwrite']
    # filepath += '/.ssh/id_rsa'
    if not os.path.exists(filepath):
        generate_key(filepath)
    filepath_pub = str(filepath) + '.pub'
    key = open(filepath_pub).read()

    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.splitlines()

    for item in csv_data_list:
        host = item.split(',')[1]
        message += deploy_key(key, host, user, ssh_password, overwrite)

    module.exit_json(
        stdout=message,
        msg="Operation Completed",
        changed=True
    )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

