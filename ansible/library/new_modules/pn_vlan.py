#!/usr/bin/python
""" PN CLI vlan-create/vlan-delete/vlan-modify """

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
from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = """
---
module: pn_vlan
author: "Pluribus Networks"
version: 2.0
short_description: CLI command to create/delete/modify VLAN.
description:
  - Execute vlan-create or vlan-delete or vlan-modify command.
  - VLANs are used to isolate network traffic at Layer 2.The VLAN identifiers
    0 and 4095 are reserved and cannot be used per the IEEE 802.1Q standard.
    The range of configurable VLAN identifiers is 2 through 4092.
options:
  pn_cliusername:
    description:
      - Provide login username if user is not root.
    required: False
    type: str
  pn_clipassword:
    description:
      - Provide login password if user is not root.
    required: False
    type: str
  pn_cliswitch:
    description:
      - Target switch(es) to run the cli on.
    required: False
    type: str
  pn_action:
    description:
      - The VLAN action to perform on the switches.
    required: True
    choices: ['create', 'delete', 'modify']
    type: str
  pn_vlanid:
    description:
      - Specify a VLAN identifier for the VLAN. This is a value between
        2 and 4092.
      - It supports single VLAN id, a list of VLANs or a VLAN Range.
    required: True
    type: str
  pn_scope:
    description:
      - Specify a scope for the VLAN.
      - Required for vlan-create.
    choices: ['fabric', 'local', 'cluster']
    default: fabric
    type: str
  pn_description:
    description:
      - Specify a description for the VLAN.
    type: str
  pn_vnet:
    description:
      - VNET for this VLAN.
    type: str
  pn_vxlan:
    description:
      - VXLAN mapped to VLAN for tunnel.
    type: str
  pn_vxlan_mode:
    description:
      - VXLAN encapsulation mode.
    type: str
    choices: ['standard', 'transparent']
  pn_public_vlan:
    description:
      - Public VLAN for VNET VLAN.
    type: str
  pn_stats:
    description:
      - Specify if you want to collect statistics for a VLAN. Statistic
        collection is enabled by default.
    type: bool
  pn_ports:
    description:
      - Specifies the switch network data port number, list of ports, or range
        of ports. Port numbers must ne in the range of 1 to 64.
    type: str
  pn_untagged_ports:
    description:
      - Specifies the ports that should have untagged packets mapped to the
        VLAN. Untagged packets are packets that do not contain IEEE 802.1Q VLAN
        tags.
    type: str
"""

EXAMPLES = """
- name: create a VLAN
  pn_vlan:
    pn_action: 'create'
    pn_vlanid: '1854, 2001, 100-105'
    pn_scope: fabric

- name: delete VLANs
  pn_vlan:
    pn_action: 'delete'
    pn_vlanid: 1854
"""

RETURN = """
final_stats:
  description: The final statistics of the module run with Pass and Fail count.
  returned: always
  type: str
unreachable:
  description: Indicates whether the switch was unreachable.
  returned: always
  type: str
failed:
  description: Indicates if the module failed.
  returned: always
  type: bool
exception:
  description: Indicates if there was an exception.
  returned: always
  type: str
summary:
  description: A set of responses in JSON object format.
  returned:always
  type: str
task:
  description: Name of the task being run.
  returned: always
  type: str
msg:
  description: A one line final output of the module.
  returned: always
  type: str
changed:
  description: Indicates whether the module applied any configurations on the target.
  returned: always
  type: bool
"""

MAX_VLAN_ID = 4092
MIN_VLAN_ID = 2
CHANGED_FLAG = []


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    cli += 'switch-local ' if cliswitch == 'local' else ' switch %s ' % (cliswitch,)
    return cli


def run_cli(module, cli):
    """
    Method to execute the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output/Error or Success msg depending upon the response from cli.
    """
    results = []
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out
    if err:
        json_msg = {
            'switch': module.params['pn_current_switch'],
            'output': u'Operation Failed: ' + ' '.join(cli)
        }
        results.append(json_msg)
        module.exit_json(
            final_stats='Failed!',
            unreachable=False,
            failed=True,
            exception='',
            summary=results,
            task='VLAN Configuration',
            stderr=err.strip(),
            msg='VLAN configuration failed',
            changed=False
        )
    else:
        return 'Success'


def get_switch_name(module):
    """
    Method to obtain fabric node name of the switch.
    :param module: The Ansible module to fetch input parameters.
    :return: fabric-node-name of the switch
    """
    cli = pn_cli(module)
    cli += ' switch-setup-show format switch-name '
    return run_cli(module, cli).split()[1]


def get_existing_vlans(module):
    """
    Method to obtain existing vlans.
    :param module: The Ansible module to fetch input parameters.
    :return: list of existing vlans.
    """
    cli = pn_cli(module)
    cli += 'vlan-show format id, no-show-headers'
    existing_vlans = run_cli(module, cli)
    return existing_vlans


def expand_range(range_str):
    """
    Method to expand a given string into range.
    :param range_str: A combination of comma separated list and range
    :return: list of values
    """
    range_to_list = []
    for value in range_str.split(','):
        if '-' not in value:
            range_to_list.append(int(value))
        else:
            l, h = map(int, value.split('-'))
            range_to_list += range(l, h+1)
    return range_to_list


def create_vlan(module, switch, vlanid):
    """
    Method to create VLAN.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the target switch
    :param vlanid: VLAN ID
    :return: message string
    """
    scope = module.params['pn_scope']
    vnet = module.params['pn_vnet']
    vxlan = module.params["pn_vxlan"]
    vxlan_mode = module.params["pn_vxlan_mode"]
    public_vlan = module.params["pn_public_vlan"]
    description = module.params['pn_description']
    stats = module.params['pn_stats']
    ports = module.params['pn_ports']
    untagged_ports = module.params['pn_untagged_ports']
    cli = pn_cli(module)
    cli += 'vlan-create id %s scope %s' % (vlanid, scope)

    if vnet:
        cli += ' vnet ' + vnet
    if vxlan:
        cli += ' vxlan ' + vxlan
    if vxlan_mode:
        cli += 'vxlan-mode ' + vxlan_mode
    if public_vlan:
        cli += ' public-vlan ' + public_vlan
    if description:
        cli += ' description ' + description
    if stats:
        cli += ' stats ' if stats is True else ' no-stats '
    if ports:
        cli += ' ports ' + ports
    if untagged_ports:
        cli += ' untagged-ports ' + untagged_ports

    output = run_cli(module, cli)

    if 'created' in output:
        return ' %s: VLAN %s created \n' % (switch, vlanid)


def delete_vlan(module, switch, vlanid):
    """
    Method to delete VLANS.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the target switch
    :param vlanid: VLAN ID
    :return: message string
    """
    cli = pn_cli(module)
    cli += 'vlan-delete id %s' % (vlanid,)
    output = run_cli(module, cli)
    if 'Success' in output:
        return ' %s: VLAN %s deleted \n' % (switch, vlanid)


def modify_vlan(module, switch, vlanid):
    """
    Method to modify existing vlans.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the target switch
    :param vlanid: VLAN ID
    :return: message string
    """
    cli = pn_cli(module)
    cli += 'vlan-modify id %s ' % (vlanid,)
    vnet = module.params['pn_vnet']
    vxlan = module.params["pn_vxlan"]
    public_vlan = module.params["pn_public_vlan"]
    description = module.params['pn_description']

    if vnet:
        cli += ' vnet ' + vnet
    if vxlan:
        cli += ' vxlan ' + vxlan
    if public_vlan:
        cli += ' public-vlan ' + public_vlan
    if description:
        cli += ' description ' + description

    output = run_cli(module, cli)
    return ' %s: %s \n' % (switch, output,)


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            pn_action=dict(required=True, type='str',
                           choices=['create', 'delete', 'modify']),
            pn_vlanid=dict(required=True, type='str'),
            pn_scope=dict(required=False, type='str',
                          choices=['fabric', 'local', 'cluster'], default='fabric'),
            pn_vnet=dict(required=False, type='str'),
            pn_vxlan=dict(required=False, type='str'),
            pn_vxlan_mode=dict(required=False, type='str'),
            pn_public_vlan=dict(required=False, type='str'),
            pn_description=dict(required=False, type='str'),
            pn_stats=dict(required=False, type='bool'),
            pn_ports=dict(required=False, type='str'),
            pn_untagged_ports=dict(required=False, type='str')
        ),
        required_if=(
            ["pn_action", "create", ["pn_vlanid", "pn_scope"]],
            ["pn_action", "delete", ["pn_vlanid"]],
            ["pn_action", "modify", ["pn_vlanid"]]
        )
    )

    # Accessing the arguments
    action = module.params['pn_action']
    vlanid = module.params['pn_vlanid']
    existing_vlans = get_existing_vlans(module)
    vlan_list = expand_range(vlanid)
    cliswitch = module.params['pn_cliswitch']
    results = []
    message = ''
    fail_count = 0
    pass_count = 0
    final_stats = ''
    global CHANGED_FLAG

    if cliswitch == 'local':
        cliswitch = get_switch_name(module)

    for vlan in vlan_list:
        if vlan not in range(MIN_VLAN_ID, MAX_VLAN_ID+1):
            json_msg = {
                'switch': cliswitch,
                'output': u'Invalid VLAN ID {}. VLAN ID must be between 2 and 4092'.format(vlan)
            }
            results.append(json_msg)
            message += 'Invalid VLAN ID {}. VLAN ID must be between 2 and 4092\n'.format(vlan)
            module.exit_json(
                final_stats='Failed!',
                unreachable=False,
                failed=True,
                exception='',
                summary=results,
                task='VLAN Configuration',
                msg=message,
                changed=False
            )

    if action == 'create':
        for vlan_id in vlan_list:
            if str(vlan_id) not in existing_vlans:
                message += create_vlan(module, cliswitch, str(vlan_id))
                json_msg = {
                    'switch': cliswitch,
                    'output': u'VLAN {} created'.format(vlan_id)
                }
                pass_count += 1
                results.append(json_msg)
                CHANGED_FLAG.append(True)
            else:
                message += 'VLAN {} already exists \n'.format(vlan_id)
                json_msg = {
                    'switch': cliswitch,
                    'output': u'VLAN {} already exists'.format(vlan_id)
                }
                fail_count += 1
                results.append(json_msg)
                CHANGED_FLAG.append(False)

    if action == 'delete':
        for vlan_id in vlan_list:
            if str(vlan_id) in existing_vlans:
                message += delete_vlan(module, cliswitch, str(vlan_id))
                json_msg = {
                    'switch': cliswitch,
                    'output': u'VLAN {} deleted'.format(vlan_id)
                }
                pass_count += 1
                results.append(json_msg)
                CHANGED_FLAG.append(True)
            else:
                message += 'VLAN {} does not exist \n'.format(vlan_id)
                json_msg = {
                    'switch': cliswitch,
                    'output': u'VLAN {} does not exist'.format(vlan_id)
                }
                fail_count += 1
                results.append(json_msg)
                CHANGED_FLAG.append(False)

    if action == 'modify':
        for vlan_id in vlan_list:
            if str(vlan_id) in existing_vlans:
                message += modify_vlan(module, cliswitch, str(vlan_id))
                json_msg = {
                    'switch': cliswitch,
                    'output': message
                }
                results.append(json_msg)
                pass_count += 1
                CHANGED_FLAG.append(True)
            else:
                message += 'VLAN {} does not exist \n'.format(vlan_id)
                json_msg = {
                    'switch': cliswitch,
                    'output': u'VLAN {} does not exist'.format(vlan_id)
                }
                fail_count += 1
                results.append(json_msg)
                CHANGED_FLAG.append(False)

    final_stats += 'Failed!   ' if fail_count else 'Pass!  '
    final_stats += 'Failed: %d  PASS: %d' % (fail_count, pass_count)

    module.exit_json(
        final_stats=final_stats,
        unreachable=False,
        msg=message,
        summary=results,
        exception='',
        task='VLAN Configuration',
        failed=True if fail_count else False,
        changed=True if True in CHANGED_FLAG else False
    )

if __name__ == '__main__':
    main()

