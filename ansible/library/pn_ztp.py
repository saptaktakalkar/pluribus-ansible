#!/usr/bin/python
""" PN CLI ZTP """

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

# TODO: Add documentation


def pn_cli(module):
    """ Build the cli command """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cli = '/usr/bin/cli --quiet '
    if username and password:
        cli += '--user %s:%s ' % (username, password)

    return cli


def auto_accept_eula(module, switch):
    # TODO
    pass


def modify_stp(module, switch, modify_flag):
    """ Enable/Disable STP """
    cli = pn_cli(module)
    cli += ' switch %s stp-modify %s ' % (switch, modify_flag)
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        return err
    else:
        return 'Success'


def enable_ports(module, switch):
    """ Enable all ports of a switch """
    cli = pn_cli(module)
    cli += ' switch %s port-config-show' % switch
    cli += ' format port no-show-headers '
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        ports = ','.join(out.split())
        cli = pn_cli(module)
        cli += ' switch %s port-config-modify %s enable ' % (switch, ports)
        cli = shlex.split(cli)
        rc, port_out, err = module.run_command(cli)

        if port_out:
            return out + port_out

        if err:
            return err
        else:
            return 'Success'

    if err:
        return err


def create_fabric(module, switch, fabric_name, fabric_network):
    """ Create a fabric with default fabric network MGMT """
    cli = pn_cli(module)
    cli += ' switch %s fabric-create name %s ' % (switch, fabric_name)
    cli += ' fabric-network %s ' % fabric_network
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        return err
    else:
        return 'Success'


def join_fabric(module, switch, fabric_name):
    """ Join to fabric """
    cli = pn_cli(module)
    cli += ' switch %s fabric-join name %s ' % (switch, fabric_name)
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        return err
    else:
        return 'Success'


def modify_fabric_network_to_inband(module, switch):
    """ Modify fabric network to in-band """
    cli = pn_cli(module)
    cli += ' switch %s modify fabric-local fabric-network in-band ' % switch
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        return err
    else:
        return 'Success'


def main():
    """ This section is for arguments parsing """

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_local_switch=dict(required=True, type='str'),
            pn_peer_switch=dict(required=True, type='str'),
            pn_switch1=dict(required=True, type='str'),
            pn_switch2=dict(required=True, type='str'),
            pn_fabric_name=dict(required=True, type='str'),
            pn_fabric_network=dict(required=False, type='str', default='mgmt'),
        )
    )

    local_switch = module.params['pn_local_switch']
    peer_switch = module.params['pn_peer_switch']
    switch1 = module.params['pn_switch1']
    switch2 = module.params['pn_switch2']
    fabric_name = module.params['pn_fabric_name']
    fabric_network = module.params['pn_fabric_network']

    for switch in [local_switch, peer_switch, switch1, switch2]:
        auto_accept_eula(module, switch)
        modify_stp(module, switch, 'disable')
        enable_ports(module, switch)

    create_fabric(module, local_switch, fabric_name, fabric_network)
    join_fabric(module, peer_switch, fabric_name)
    join_fabric(module, switch1, fabric_name)
    join_fabric(module, switch2, fabric_name)

    # TODO: For L2: Auto-vlag
    # TODO: For L3: Auto configure link IPs

    for switch in [local_switch, peer_switch, switch1, switch2]:
        modify_fabric_network_to_inband(module, switch)

    module.exit_json(
        # TODO: Return appropriate JSON
    )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

