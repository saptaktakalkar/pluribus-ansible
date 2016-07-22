#!/usr/bin/python
""" PN CLI vnet-create/vnet-delete """

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_vnet
author: "Pluribus Networks"
short_description: CLI command to create/delete vnet.
description:
  - Execute vnet-create or vnet-delete command.
  - A fabric, cluster, or standalone switch can be virtualized into tenant 
    networks called virtual networks (VNETs). This command creates a new VNET.
options:
  pn_cliusername:
    description:
      - Login username
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password
    required: true
    type: str
  pn_cliswitch:
    description:
    - Target switch to run the cli on.
  pn_command:
    description:
      - The C(pn_command) takes the vnet-create/delete command as value.
    required: true
    choices: vnet-create, vnet-delete
    type: str
  pn_name:
    description:
      - Specify the name of the virtual network(VNET).
    required: true
    type: str
  pn_scope:
    description:
      - Specify the scope of the virtual network(VNET).
    required_if: vnet-create
    choices: local, fabric
    type: str
  pn_vrg:
    description:
      - Specify the name of the virtual resource group(VRG).
    type: str
  pn_num_vlans:
    description:
      - Specify the number of VLANs to assign to the VNET. Using this parameter
        allows you to assign a group of VLANs rather than specific VLANs.
    type: str
  pn_vlans:
    description:
      - Specify the list of VLANs to assign to the VNET. You can specify a list 
        or range of VLANs that the VNET assigns to VNET interfaces.
    type: str
  pn_managed_ports:
    description:
      - Specify the list of managed ports on the VNET.
    type: str
  pn_ports:
    description:
      - Specify the ports for the VNET.
    type: str
  pn_config_admin:
    description:
      - Specify an administrator for the VNET.
    choices: config-admin, no-config-admin.
    type: str
  pn_admin:
    description:
      - Specify the username for the admin role
    type: str
  pn_vnet_mgr_name:
    description:
      - Specify the name of the VNET manager. If you dont specify a name,
        one is automatically configured.
    type: str
  pn_vnet_mgr_storage_pool:
    description:
      - Specify the storage pool for the VNET.
  pn_quiet:
    description:
      - Enable/disable system information.
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create a VNET
  pn_vnet:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vnet-create'
    pn_name: Myvnet
    pn_scope: fabric

- name: delete VNET
  pn_vnet:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vnet-delete'
    pn_name: Myvnet
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vnet command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vnet command.
  returned: on error
  type: list
rc:
  description: return code of the module.
  returned: 0 on success, 1 on error
  type: int
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def main():
    """ This section is for argument parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str',
                                aliases=['username']),
            pn_clipassword=dict(required=True, type='str',
                                aliases=['password']),
            pn_cliswitch=dict(required=False, type='str', aliases=['switch']),
            pn_command=dict(required=True, type='str',
                            choices=['vnet-create', 'vnet-delete'],
                            aliases=['command']),
            pn_name=dict(required=True, type='str', aliases=['name']),
            pn_scope=dict(type='str', choices=['local', 'fabric'],
                          aliases=['scope']),
            pn_vrg=dict(type='str', aliases=['vrg']),
            pn_vlan_nums=dict(type='str', aliases=['num_vlans']),
            pn_managed_ports=dict(type='str', aliases=['managed_ports']),
            pn_ports=dict(type='str', aliases=['ports']),
            pn_vlanports=dict(type='str', aliases=['vlan_ports']),
            pn_config_admin=dict(type='str',
                                 choices=['config-admin', 'no-config-admin'],
                                 aliases=['config_admin']),
            pn_admin_name=dict(type='str', aliases=['admin_name']),
            pn_vnet_mgr_name=dict(type='str', aliases=['vnet_mgr_name']),
            pn_vnet_mgr_storage_pool=dict(type='str',
                                          aliases=['vnet_mgr_storage_pool']),
            pn_quiet=dict(default=True, type='bool', aliases=['quiet'])
        ),
        required_if=(
            ["pn_command", "vnet-create", ["pn_name", "pn_scope"]],
            ["pn_command", "vnet-delete", ["pn_name"]]
        )
    )

    # Argument accessing
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    switch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    name = module.params['pn_name']
    scope = module.params['pn_scope']
    vrg = module.params['pn_vrg']
    vlan_nums = module.params['pn_vlan_nums']
    managed_ports = module.params['pn_managed_ports']
    ports = module.params['pn_ports']
    vlanports = module.params['pn_vlanports']
    config_admin = module.params['pn_config_admin']
    admin_name = module.params['pn_admin_name']
    vnet_mgr_name = module.params['pn_vnet_mgr_name']
    vnet_mgr_storage_pool = module.params['pn_vnet_mgr_storage_pool']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    if switch:
        cli += ' switch ' + switch

    cli += ' ' + command + ' name ' + name

    if scope:
        cli += ' scope ' + scope

    if vrg:
        cli += ' vrg ' + vrg

    if vlan_nums:
        cli += ' num_-vlans ' + vlan_nums

    if managed_ports:
        cli += ' managed-ports ' + managed_ports

    if ports:
        cli += ' ports ' + ports

    if vlanports:
        cli += ' vlan-ports ' + vlanports

    if config_admin:
        cli += ' ' + config_admin

    if admin_name:
        cli += ' admin ' + admin_name

    if vnet_mgr_name:
        cli += ' vnet-mgr-name ' + vnet_mgr_name

    if vnet_mgr_storage_pool:
        cli += ' vnet-mgr-storage-pool ' + vnet_mgr_storage_pool

    # Running the CLI command
    vnetcmd = shlex.split(cli)
    response = subprocess.Popen(vnetcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    # Response in JSON format
    if err:
        module.exit_json(
            command=cli,
            stderr=err.rstrip("\r\n"),
            rc=1,
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            stdout=out.rstrip("\r\n"),
            rc=0,
            changed=True
        )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
