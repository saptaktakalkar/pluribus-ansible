#!/usr/bin/python
""" PN Vrouter Creation """

#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import shlex

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_vrouter_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to create vrouters.
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
    pn_switch:
      description:
        - Name of the switch on which this task is currently getting executed.
      required: True
      type: str
"""

EXAMPLES = """
- name: Create Vrouters
  pn_svi_configuration:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_switch: "{{ inventory_hostname }}"
"""

RETURN = """
summary:
  description: It contains output of each configuration along with switch name.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
unreachable:
  description: Indicates whether switch was unreachable to connect.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
exception:
  description: Describes error/exception occurred while executing CLI command.
  returned: always
  type: str
task:
  description: Name of the task getting executed on switch.
  returned: always
  type: str
msg:
  description: Indicates whether configuration made was successful or failed.
  returned: always
  type: str
"""

CHANGED_FLAG = []


def pn_cli(module):
    """
    Generate the cli portion to launch the Netvisor cli.
    :param module: The Ansible module to fetch username and password.
    :return: The cli string for further processing.
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def run_cli(module, cli):
    """
    Execute the cli command on the target node(s) and returns the output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output or Error msg depending upon the response from cli else None.
    """
    results = []
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out
    if err:
        json_msg = {
            'switch': '',
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception=err.strip(),
            summary=results,
            task='Create vrouter',
            msg='Vrouter creation failed',
            changed=False
        )
    else:
        return 'Success'


def create_vrouter(module, vnet_name):
    """
    Create a hardware vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param vnet_name: Vnet name required for vrouter creation.
    :return: String describing if vrouter got created or not.
    """
    global CHANGED_FLAG
    output = ''
    new_vrouter = False
    cli_orig = pn_cli(module)
    vrrp_id = module.params['pn_vrrp_id']
    switch_list = module.params['pn_switch_list']

    # Check if vrouter already exists
    for switch in switch_list:
        cli = cli_orig
        cli += ' switch ' + switch
        clicopy = cli
        vrouter_name = switch + '-vrouter'

        cli = clicopy
        cli += ' vrouter-show format name no-show-headers '
        existing_vrouter_names = run_cli(module, cli)

        if 'Success' not in existing_vrouter_names:
            existing_vrouter_names = existing_vrouter_names.split()
            if vrouter_name not in existing_vrouter_names:
                new_vrouter = True

        if new_vrouter or 'Success' in existing_vrouter_names:
            cli = clicopy
            cli += ' vrouter-create name %s ' % vrouter_name
            cli += ' vnet %s ' % (vnet_name)
            if vrrp_id:
                cli += ' hw-vrrp-id %s ' % vrrp_id
            cli += ' enable router-type hardware '
            run_cli(module, cli)
            CHANGED_FLAG.append(True)
            output += '%s: Created vrouter with name %s\n' % (switch, vrouter_name)

    return output


def assign_loopback_ip(module, loopback_address):
    """
    Method to add loopback interface to vrouters.
    :param module: The Ansible module to fetch input parameters.
    :param loopback_address: The loopback ip to be assigned.
    :return: String describing if loopback ips got assigned or not.
    """
    global CHANGED_FLAG
    output = ''
    address = loopback_address.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'

    cli = pn_cli(module)
    clicopy = cli
    switch_list = module.params['pn_switch_list']

    vrouter_count = int(address[3])
    for switch in switch_list:
        vrouter = switch + '-vrouter'
        ip = static_part + str(vrouter_count)

        cli = clicopy
        cli += ' vrouter-modify name %s router-id %s ' % (vrouter, ip)
        if 'Success' in run_cli(module, cli):
            output += ' %s: Added router-id %s \n' % (switch, ip)

        cli = clicopy
        cli += ' vrouter-loopback-interface-show ip ' + ip
        cli += ' format switch no-show-headers '
        existing_vrouter = run_cli(module, cli).split()

        if vrouter not in existing_vrouter:
            cli = clicopy
            cli += ' vrouter-loopback-interface-add vrouter-name '
            cli += vrouter
            cli += ' ip ' + ip
            run_cli(module, cli)
            CHANGED_FLAG.append(True)

        output += ' %s: Added loopback ip %s to %s \n' % (switch, ip, vrouter)
        vrouter_count += 1

    return output


def vrouter_creation(module):
    """
    Method to create vrouter
    :param module: The Ansible module to fetch input parameters.
    :return: String describing whether vrouter got created or not.
    """
    global CHANGED_FLAG
    output = ''

    cli = pn_cli(module)
    cli += ' fabric-node-show format fab-name no-show-headers '
    fabric_name = list(set(run_cli(module, cli).split()))[0]

    vnet_name = fabric_name + '-global'
    loopback_address = module.params['pn_loopback_ip']

    output += create_vrouter(module, vnet_name)
    if loopback_address:
        output += assign_loopback_ip(module, loopback_address)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_loopback_ip=dict(required=False, type='str', default=''),
            pn_vrrp_id=dict(required=False, type='str', default=''),
            pn_switch_list=dict(required=False, type='list'),
        )
    )

    global CHANGED_FLAG
    results = []
    message = ''

    message += vrouter_creation(module)

    for line in message.splitlines():
        if ': ' in line:
            return_msg = line.split(':')
            json_msg = {'switch' : return_msg[0].strip(), 'output' : return_msg[1].strip()}
            results.append(json_msg)

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='Vrouter creation succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Create vrouter'
    )

if __name__ == '__main__':
    main()
