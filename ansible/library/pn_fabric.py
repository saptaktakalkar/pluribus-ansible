#!/usr/bin/python
""" PN-CLI module for fabric-create/fabric-join"""

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

import shlex
import subprocess


def main():
    """Module instantiation"""
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_fabric_command=dict(required=True, type='str',
                                   choices=["fabric-create", "fabric-join"]),
            pn_fabric_name=dict(required=True, type='str')
        )
    )

    # Accessing arguments
    cliusername = module.params["pn_cliusername"]
    clipassword = module.params["pn_clipassword"]
    fabric_command = module.params["pn_fabric_command"]
    fabric_name = module.params["pn_fabric_name"]

    # Building the CLI
    fabric = ('/usr/bin/cli --user ' + cliusername + ':' + clipassword +
              ' ' + fabric_command + ' ' + fabric_name)
    # Running the CLI
    command = shlex.split(fabric)
    response = subprocess.Popen(command, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if err:
        module.exit_json(
            command=fabric,
            stderr=err.rstrip("\r\n"),
            changed=False
        )
    else:
        module.exit_json(
            command=fabric,
            stdout=out.rstrip("\r\n"),
            changed=True
        )
# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
