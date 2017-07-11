#!/usr/bin/python
""" PN Dlink Fabric Creation """

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

import binascii
import shlex
import socket
import time

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: dlink_fabric_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to perform fabric creation/join.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Disable STP
        - Enable all ports
        - Create/Join fabric
        - Enable STP
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
    pn_spine_list:
      description:
        - Specify list of Spine hosts
      required: False
      type: list
    pn_leaf_list:
      description:
        - Specify list of leaf hosts
      required: False
      type: list
    pn_inband_ip:
      description:
        - Inband ips to be assigned to switches starting with this value.
      required: False
      default: 172.16.0.0/24.
      type: str
    pn_current_switch:
      description:
        - Name of the switch on which this task is currently getting executed.
      required: False
      type: str
    pn_mgmt_ip:
      description:
        - Specify mgmt-ip of the switch.
      required: False
      type: str
    pn_host_ips:
      description:
        - Specify ips of all hosts/switches separated by comma.
      required: True
      type: str
    pn_toggle_40g:
      description:
        - Flag to indicate if 40g ports should be converted to 10g ports or not.
      required: False
      default: True
      type: bool
"""

EXAMPLES = """
- name: Fabric creation/join
    dlink_fabric_creation:
      pn_cliusername: "{{ USERNAME }}"
      pn_clipassword: "{{ PASSWORD }}"
      pn_current_switch: "{{ inventory_hostname }}"
      pn_spine_list: "{{ groups['spine'] }}"
      pn_leaf_list: "{{ groups['leaf'] }}"
      pn_mgmt_ip: "{{ ansible_host }}"
      pn_host_ips: "{{ groups['all'] |
        map('extract', hostvars, ['ansible_host']) | join(',') }}"
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
            'switch': module.params['pn_current_switch'],
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception=err.strip(),
            summary=results,
            task='Fabric creation',
            msg='Fabric creation failed',
            changed=False
        )
    else:
        return None


def assign_inband_ip(module):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing in-band ip got assigned or not.
    """
    global CHANGED_FLAG
    output = ''
    address = module.params['pn_inband_ip'].split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    switches_list = []
    spines = module.params['pn_spine_list']
    leafs = module.params['pn_leaf_list']
    switch = module.params['pn_current_switch']

    if spines:
        switches_list += spines

    if leafs:
        switches_list += leafs

    if switches_list:
        ip_count = switches_list.index(switch) + 1
        ip = static_part + str(ip_count) + '/' + subnet

        # Get existing in-band ip.
        cli = pn_cli(module)
        clicopy = cli
        cli += ' switch-local switch-setup-show format in-band-ip '
        existing_inband_ip = run_cli(module, cli)

        if ip not in existing_inband_ip:
            cli = clicopy
            cli += ' switch-local switch-setup-modify '
            cli += ' in-band-ip ' + ip
            run_cli(module, cli)
            CHANGED_FLAG.append(True)
            output += 'Assigned in-band ip ' + ip

        return output

    return 'Could not assign in-band ip'


def toggle_40g_local(module):
    """
    Method to toggle 40g ports to 10g ports.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of all run_cli() commands.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch-local lldp-show format local-port no-show-headers '
    local_ports = run_cli(module, cli).split()

    cli = clicopy
    cli += ' switch-local port-config-show speed 40g '
    cli += ' format port no-show-headers '
    ports_40g = run_cli(module, cli)
    if ports_40g is not None and len(ports_40g) > 0:
        ports_40g = ports_40g.split()
        ports_to_modify = list(set(ports_40g) - set(local_ports))

        for port in ports_to_modify:
            next_port = str(int(port) + 1)
            cli = clicopy
            cli += ' switch-local'
            cli += ' port-show port %s format bezel-port' % next_port
            cli += ' no-show-headers'
            bezel_port = run_cli(module, cli)

            if bezel_port is not None:
                bezel_port = bezel_port.split()[0]

                if '.2' in bezel_port:
                    end_port = int(port) + 3
                    range_port = port + '-' + str(end_port)

                    cli = clicopy
                    cli += ' switch-local port-config-modify port %s ' % port
                    cli += ' disable '
                    output += 'port ' + port + ' disabled'
                    run_cli(module, cli)

                    cli = clicopy
                    cli += ' switch-local port-config-modify port %s ' % port
                    cli += ' speed 10g '
                    output += 'port ' + port + ' converted to 10g'
                    run_cli(module, cli)

                    cli = clicopy
                    cli += ' switch-local port-config-modify '
                    cli += ' port %s enable ' % range_port
                    output += 'port range_port ' + range_port + '  enabled'
                    run_cli(module, cli)

        time.sleep(10)
        CHANGED_FLAG.append(True)

    return output


def enable_ports(module):
    """
    Method to enable all ports of a switch.
    :param module: The Ansible module to fetch input parameters.
    """
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch-local port-config-show format enable no-show-headers '
    if 'off' in run_cli(module, cli).split():
        cli = clicopy
        cli += ' switch-local port-config-show format port no-show-headers '
        out = run_cli(module, cli)

        cli = clicopy
        cli += ' switch-local port-config-show format port speed 40g '
        cli += ' no-show-headers '
        out_40g = run_cli(module, cli)
        out_remove10g = []

        if len(out_40g) > 0 and out_40g != 'Success':
            out_40g = out_40g.split()
            out_40g = list(set(out_40g))
            if len(out_40g) > 0:
                for port_number in out_40g:
                    out_remove10g.append(str(int(port_number) + int(1)))
                    out_remove10g.append(str(int(port_number) + int(2)))
                    out_remove10g.append(str(int(port_number) + int(3)))

        if out:
            out = out.split()
            out = set(out) - set(out_remove10g)
            out = list(out)
            if out:
                ports = ','.join(out)
                cli = clicopy
                cli += ' switch-local port-config-modify port %s enable ' % (
                    ports)
                run_cli(module, cli)


def modify_stp(module, modify_flag):
    """
    Method to enable/disable STP (Spanning Tree Protocol) on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param modify_flag: Enable/disable flag to set.
    """
    cli = pn_cli(module)
    cli += ' switch-local stp-show format enable '
    current_state = run_cli(module, cli).split()[1]

    state = 'yes' if modify_flag == 'enable' else 'no'

    if current_state == state:
        cli = pn_cli(module)
        cli += ' switch-local stp-modify ' + modify_flag
        run_cli(module, cli)


def enable_web_api(module):
    """
    Enable web api on a switch.
    :param module: The Ansible module to fetch input parameters.
    """
    cli = pn_cli(module)
    cli += ' admin-service-modify web if mgmt '
    run_cli(module, cli)


def configure_control_network(module):
    """
    Configure the fabric control network to mgmt.
    :param module: The Ansible module to fetch input parameters.
    """
    network = 'mgmt'
    cli = pn_cli(module)
    cli += ' fabric-info format control-network '
    current_control_network = run_cli(module, cli).split()[1]

    if current_control_network != network:
        cli = pn_cli(module)
        cli += ' fabric-local-modify control-network ' + network
        run_cli(module, cli)


def get_fabric_name_using_ip(ip):
    """
    Get fabric name using hex representation of an ip address.
    :param ip: IP address to convert to hex
    :return: Fabric name prefixed with 'fab-', followed by hex of ip
    """
    return 'fab-' + binascii.hexlify(socket.inet_aton(ip))


def get_switch_name_to_ip_dict(module):
    """
    Get the dict containing switch_name:switch_ip pairs for all switches.
    :param module: The Ansible module to fetch input parameters.
    :return: dict containing switch_name:switch_ip pairs for all switches.
    """
    hosts = module.params['pn_spine_list'] + module.params['pn_leaf_list']
    count = 0
    host_ip_dict = {}

    for ip in module.params['pn_host_ips'].split(','):
        host_ip_dict[hosts[count]] = ip
        count += 1

    return host_ip_dict


def create_fabric(module, fabric_name):
    """
    Create a fabric
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to create.
    :return: 'Created fabric fabric_name'
    """
    cli = pn_cli(module)
    cli += ' fabric-create name %s fabric-network mgmt ' % fabric_name
    run_cli(module, cli)
    CHANGED_FLAG.append(True)
    return 'Created fabric {}'.format(fabric_name)


def join_fabric(module, fabric_name):
    """
    Join existing fabric
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to join to.
    :return: 'Joined fabric fabric_name'
    """
    cli = pn_cli(module)
    cli += ' fabric-join name %s ' % fabric_name
    run_cli(module, cli)
    CHANGED_FLAG.append(True)
    return 'Joined fabric {}'.format(fabric_name)


def configure_fabric(module):
    """
    Create/join fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if fabric got created/joined/already configured.
    """
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    switch = module.params['pn_current_switch']
    switch_ip = module.params['pn_mgmt_ip']
    find_cluster = True
    is_spine = False

    cli = pn_cli(module)
    cli += ' fabric-info format name no-show-headers '
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    # Above fabric-info cli command will throw an error, if switch is not part
    # of any fabric. So if err, we need to create/join the fabric.
    if err:
        if switch in spine_list:
            is_spine = True
            if len(spine_list) == 1:
                find_cluster = False
        elif switch in leaf_list:
            if len(leaf_list) == 1:
                find_cluster = False

        # Clustered switches will be in same fabric.
        # So if a switch is going to be a part of a cluster, then check whether
        # that switch need to create a fabric or need to join the fabric
        # created by it's clustered switch.
        if find_cluster:
            cli = pn_cli(module)
            cli += ' lldp-show format sys-name no-show-headers '
            sys_names = run_cli(module, cli)

            if sys_names is not None:
                sys_names = list(set(sys_names.split()))
                cluster_node = None
                for sys in sys_names:
                    if is_spine:
                        if sys in spine_list:
                            cluster_node = sys
                            break
                    else:
                        if sys in leaf_list:
                            cluster_node = sys
                            break

                if cluster_node is not None:
                    host_ip_dict = get_switch_name_to_ip_dict(module)
                    cluster_node_ip = host_ip_dict[cluster_node]
                    fabric_name = get_fabric_name_using_ip(cluster_node_ip)

                    cli = pn_cli(module)
                    cli += ' fabric-show format name no-show-headers '
                    existing_fabrics = run_cli(module, cli).split()

                    if fabric_name in existing_fabrics:
                        output = join_fabric(module, fabric_name)
                    else:
                        fabric_name = get_fabric_name_using_ip(switch_ip)
                        output = create_fabric(module, fabric_name)
                else:
                    fabric_name = get_fabric_name_using_ip(switch_ip)
                    output = create_fabric(module, fabric_name)
            else:
                fabric_name = get_fabric_name_using_ip(switch_ip)
                output = create_fabric(module, fabric_name)

        # If a switch is not part of any cluster then create a unique fabric
        # for it.
        else:
            fabric_name = get_fabric_name_using_ip(switch_ip)
            output = create_fabric(module, fabric_name)
    else:
        output = 'Fabric already configured'

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(argument_spec=dict(
        pn_cliusername=dict(required=False, type='str'),
        pn_clipassword=dict(required=False, type='str', no_log=True),
        pn_spine_list=dict(required=False, type='list', default=[]),
        pn_leaf_list=dict(required=False, type='list', default=[]),
        pn_inband_ip=dict(required=False, type='str', default='172.16.0.0/24'),
        pn_current_switch=dict(required=False, type='str'),
        pn_mgmt_ip=dict(required=False, type='str'),
        pn_host_ips=dict(required=True, type='str'),
        pn_toggle_40g=dict(required=False, type='bool', default=True), )
    )

    global CHANGED_FLAG
    results = []
    current_switch = module.params['pn_current_switch']

    # Create/join fabric
    out = configure_fabric(module)
    results.append({
        'switch': current_switch,
        'output': out
    })

    # Configure fabric control network to mgmt
    configure_control_network(module)

    # Enable web api
    enable_web_api(module)

    # Disable STP
    modify_stp(module, 'disable')

    # Enable all ports
    enable_ports(module)

    # Convert 40g ports to 10g speed
    if module.params['pn_toggle_40g']:
        if toggle_40g_local(module):
            results.append({
                'switch': current_switch,
                'output': 'Toggled 40G ports to 10G'
            })

    # Assign in-band ips.
    out = assign_inband_ip(module)
    if out:
        results.append({
            'switch': current_switch,
            'output': out
        })

    # Enable STP
    modify_stp(module, 'enable')

    # Exit the module and return the required JSON
    module.exit_json(
        unreachable=False,
        msg='Fabric creation succeeded',
        summary=results,
        exception='',
        task='Fabric creation',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )

if __name__ == '__main__':
    main()

