#!/usr/bin/python
""" PN DCI """

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

from ansible.module_utils.basic import AnsibleModule
import shlex
import time

DOCUMENTATION = """
---
module: pn_dci
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to implement a DCI.
description:
    This module is to plan and implement a DCI architecture.
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
    pn_fabric_name:
      description:
        - Specify name of the fabric.
      required: False
      type: str
    pn_spine_list:
      description:
        - Specify list of Spine hosts
      required: True
      type: list
    pn_leaf_list:
      description:
        - Specify list of leaf hosts
      required: True
      type: list
    pn_bgp_redistribute:
      description:
        - Specify bgp_redistribute value to be added to vrouter.
      required: False
      type: str
      choices: ['none', 'static', 'connected', 'rip', 'ospf']
      default: 'connected'
    pn_bgp_maxpath:
      description:
        - Specify bgp_maxpath value to be added to vrouter.
      required: False
      type: str
      default: '16'
    pn_bgp_as_range:
      description:
        - Specify bgp_as_range value to be added to vrouter.
      required: False
      type: str
      default: '65000'
    pn_csv_data:
      description:
        - Specify commands to be run on the switches
        required: True
        type: str
    pn_current_switch:
      description:
        - Specify name of the current switch
        required: True
        type: str
    pn_inband_ip:
      description:
        - Specify the inband ip address
        required: False
        type: str
    pn_bgp_ip:
      description:
        - Specify the bgp ip for creating neighbor
        required: False
        type: str
    pn_accept_eula:
      description:
        - Flag to accept eula
        required: True
        type: bool
"""

EXAMPLES = """
- name: Implement DCI
  pn_dci:
    pn_accept_eula: False
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_fabric_name: 'dci_fabric'
    pn_spine_list: "{{ groups['spine'] }}"
    pn_leaf_list: "{{ groups['leaf'] }}"
    pn_current_switch: "{{ inventory_hostname }}"
    pn_inband_ip: '172.16.0.0/24'
    pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
"""

RETURN = """
stdout:
  description: The set of responses for each command.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
"""

CHANGED_FLAG = []


def pn_cli(module):
    """
    Method to generate the cli portion to launch the Netvisor cli.
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
    Method to execute the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output/Error or Success msg depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)
    if out:
        return out

    if err:
        module.exit_json(
            error='1',
            failed=True,
            stderr=err.strip(),
            msg='Operation Failed: ' + str(cli),
            changed=False
        )
    else:
        return 'Success'


def auto_accept_eula(module):
    """
    Method to accept the EULA when we first login to a new switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    password = module.params['pn_clipassword']
    cli = ' /usr/bin/cli --quiet --skip-setup eula-show '
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if err:
        cli = '/usr/bin/cli --quiet'
        cli += ' --skip-setup --script-password '
        cli += ' switch-setup-modify password ' + password
        cli += ' eula-accepted true '
        return run_cli(module, cli)
    elif out:
        return ' EULA has been accepted already '


def update_switch_names(module, switch_name):
    """
    Method to update switch names.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name to assign to the switch.
    :return: String describing switch name got modified or not.
    """
    cli = pn_cli(module)
    cli += ' switch-setup-show format switch-name '
    if switch_name in run_cli(module, cli).split()[1]:
        return ' Switch name is same as hostname! '
    else:
        cli = pn_cli(module)
        cli += ' switch-setup-modify switch-name ' + switch_name
        run_cli(module, cli)
        return ' Updated switch name to match hostname! '


def assign_inband_ip(module, inband_ip):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :param inband_ip: In-band ip to be assigned to the switch.
    :return: String describing if in-band ip got assigned or not.
    """
    supernet = 4
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']

    switch_position = int(leaf_list.index(current_switch))
    ip_count = (supernet * switch_position) + 1

    address = inband_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    ip = static_part + str(ip_count) + '/' + subnet

    cli = pn_cli(module)
    cli += 'switch-setup-modify in-band-ip %s ' % ip

    if 'Setup completed successfully' in run_cli(module, cli):
        return '%s: In-band ip assigned with ip %s \n' % (current_switch, ip)

    return ''


def find_clustered_switches(module):
    """
    Method to find clustered switches from the input csv file.
    :param module: The Ansible module to fetch input parameters.
    :return: It returns a dict whose first value is list of pairs of cluster
    and second is list of switches in cluster.
    """
    csv_data = module.params['pn_csv_data'].replace(' ', '')
    csv_data = csv_data.split('\n')
    cluster_dict_info = {}
    cluster_list = []
    cluster_switches = []

    for line in csv_data:
        if line != '':
            line = line.split(',')
            cluster_node_1 = line[2]
            cluster_node_2 = line[3]

            if cluster_node_2 != '':
                temp_list = [cluster_node_1, cluster_node_2]
                if temp_list not in cluster_list:
                    cluster_switches.append(cluster_node_1)
                    cluster_switches.append(cluster_node_2)
                    cluster_list.append(temp_list)

    cluster_dict_info[0] = cluster_list
    cluster_dict_info[1] = cluster_switches

    return cluster_dict_info


def fabric_inband_net_create(module, inband_static_part, subnet):
    """
    Method to create fabric in-band network.
    :param module: The Ansible module to fetch input parameters.
    :param inband_static_part: In-band ip address till third octet.
    :param subnet: Subnet mask of in-band ip address.
    :return: String describing if fabric in-band network got created or not.
    """
    global CHANGED_FLAG
    output = ''
    supernet = 4
    switch_count = 0
    cli = pn_cli(module)
    clicopy = cli

    while switch_count < len(module.params['pn_leaf_list']):
        ip_count = switch_count * supernet
        inband_network_ip = inband_static_part + str(ip_count) + '/' + subnet

        cli = clicopy
        cli += 'fabric-in-band-network-show format network no-show-headers'
        existing_networks = run_cli(module, cli).split()

        if inband_network_ip not in existing_networks:
            cli = clicopy
            cli += 'fabric-in-band-network-create network ' + inband_network_ip
            if 'Success' in run_cli(module, cli):
                output += ' Fabric in-band network created for %s \n' % (
                    inband_network_ip
                )
                CHANGED_FLAG.append(True)
        else:
            output += ' Fabric in-band network %s already exists\n' % (
                inband_network_ip
            )

        switch_count += 1

    return output


def join_fabric(module, switch_ip):
    """
    Method to join existing fabric by pointing to in-band ip of first switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch_ip: In-band ip of the first/originator switch.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    clicopy = cli

    cli += ' fabric-info format name no-show-headers'
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if err:
        cli = clicopy
        cli += ' fabric-join switch-ip %s ' % switch_ip
    elif out:
        return ' Already in a fabric\n'

    return run_cli(module, cli)


def create_and_configure_vrouter(module, bgp_nic_ip, neighbor_ip, remote_switch,
                                 cluster_list, non_clustered_switches):
    """
    Method to create and configure vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_nic_ip: Bgp_nic_ip for the vrouter creation.
    :param neighbor_ip: Neighbor_ip for the vrouter creation.
    :param remote_switch: Remote switch for the vrouter creation.
    :param cluster_list: List of clustered switch pairs.
    :param non_clustered_switches: List of non_clustered switches.
    :return: String describing vrouter creation details.
    """
    global CHANGED_FLAG
    output = ''
    vrouter_name = module.params['pn_current_switch'] + '-vrouter'
    bgp_as_range = module.params['pn_bgp_as_range']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    bgp_redistribute = module.params['pn_bgp_redistribute']
    bgp_max_path = module.params['pn_bgp_max_path']
    non_clustered_switches_count = len(non_clustered_switches)

    cli = pn_cli(module)
    clicopy = cli

    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += 'switch-setup-show format in-band-ip no-show-headers'
        inband_ip = run_cli(module, cli)

        address = inband_ip.split(':')[1]
        address = address.replace(' ', '')
        address = address.split('.')
        static_part = str(address[0]) + '.' + str(address[1]) + '.'
        static_part += str(address[2]) + '.'
        last_octet = str(address[3]).split('/')
        netmask = last_octet[1]
        gateway_ip = int(last_octet[0]) + 1
        ip = static_part + str(gateway_ip)

        # remote-as for leaf is always spine1 and for spine is always leaf1
        if current_switch in spine_list:
            bgp_as = bgp_as_range
            if remote_switch in non_clustered_switches:
                remote_as = int(bgp_as_range) + 1 + \
                            non_clustered_switches.index(remote_switch)
            else:
                cluster_count = 0
                stop_flag = 0
                while cluster_count < len(cluster_list) and stop_flag == 0:
                    if remote_switch in cluster_list[cluster_count]:
                        remote_as = int(non_clustered_switches_count) + 1 + \
                                    cluster_count + int(bgp_as_range)
                        stop_flag += 1
                    cluster_count += 1
            remote_as = str(remote_as)

            cli = clicopy
            cli += 'port-show hostname %s format port, no-show-headers' % (
                leaf_list[0])
            ports = run_cli(module, cli).split()

            cli = clicopy
            cli += 'trunk-show ports %s format trunk-id, no-show-headers ' % (
                ports[0])
            trunk_id = run_cli(module, cli)

            if len(trunk_id) == 0 or trunk_id == 'Success':
                l3_port = ports[0]
            else:
                l3_port = trunk_id

            fabric_network_addr = static_part + str(0) + '/' + netmask

        else:

            if current_switch in non_clustered_switches:
                bgp_as = int(bgp_as_range) + 1 + non_clustered_switches.index(
                    current_switch)
            else:
                cluster_count = 0
                stop_flag = 0
                while cluster_count < len(cluster_list) and stop_flag == 0:
                    if current_switch in cluster_list[cluster_count]:
                        bgp_as = int(non_clustered_switches_count) + 1 + \
                                 cluster_count + int(bgp_as_range)
                        stop_flag += 1
                    cluster_count += 1
            remote_as = bgp_as_range
            bgp_as = str(bgp_as)

            cli = clicopy
            cli += 'port-show hostname %s format port, no-show-headers' % \
                   spine_list[0]
            ports = run_cli(module, cli).split()

            cli = clicopy
            cli += 'trunk-show ports %s format trunk-id, no-show-headers ' % (
                ports[0]
            )
            trunk_id = run_cli(module, cli)
            if len(trunk_id) == 0 or trunk_id == 'Success':
                l3_port = ports[0]
            else:
                l3_port = trunk_id

            fabric_network_addr = static_part + str(0) + '/' + netmask

        cli = clicopy
        cli += 'fabric-comm-vrouter-bgp-create name %s bgp-as %s' % (
            vrouter_name, bgp_as
        )
        cli += ' bgp-redistribute %s bgp-max-paths %s' % (bgp_redistribute,
                                                          bgp_max_path)
        cli += ' bgp-nic-ip %s bgp-nic-l3-port %s' % (bgp_nic_ip, l3_port)
        cli += ' neighbor %s remote-as %s' % (neighbor_ip, remote_as)

        if (current_switch in spine_list and
                spine_list.index(current_switch) == 0):
            pass
        else:
            cli += ' fabric-network %s' % fabric_network_addr

        cli += ' in-band-nic-ip %s in-band-nic-netmask %s bfd' % (ip, netmask)
        cli += ' allowas-in'
        output += '%s: Fab-comm command executed with output- ' % current_switch
        output += str(run_cli(module, cli))
        CHANGED_FLAG.append(True)
    else:
        output += '%s: Vrouter already exist \n' % current_switch

    return output


def implement_dci(module):
    """
    Method to implement DCI.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing details of DCI implementation.
    """
    global CHANGED_FLAG
    output = ''
    supernet = 4
    inband_ip = module.params['pn_inband_ip']
    bgp_ip = module.params['pn_bgp_ip']
    leaf_list = module.params['pn_leaf_list']
    switch_count = len(leaf_list)
    fabric_name = module.params['pn_fabric_name']

    # Assign in-band ip.
    output += assign_inband_ip(module, inband_ip)

    address = bgp_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'

    address = inband_ip.split('.')
    inband_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    inband_static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    cluster_dict_info = find_clustered_switches(module)
    cluster_list = cluster_dict_info[0]
    cluster_switches = cluster_dict_info[1]
    cluster_list = sorted(cluster_list)
    non_clustered_switches = list(sorted(set(leaf_list) - set(
        cluster_switches)))

    cli = pn_cli(module)
    clicopy = cli

    for switch in leaf_list:
        switch_index = leaf_list.index(switch)
        if switch_index == 0:
            cli = clicopy
            cli += 'fabric-show format name no-show-headers'
            existing_fabric = run_cli(module, cli).split()

            # Create fabric if not already created.
            if fabric_name not in existing_fabric:
                cli = clicopy
                cli += 'fabric-create name %s ' % fabric_name
                cli += ' fabric-network in-band control-network in-band '
                output += ' %s: %s ' % (switch, run_cli(module, cli))
                CHANGED_FLAG.append(True)
            else:
                output += ' %s: Fabric already exists\n' % switch

            # Indicate all subnets of the in-band interfaces of switches,
            # that will be part of the fabric.
            output += fabric_inband_net_create(module, inband_static_part,
                                               subnet)
        else:
            switch_ip = inband_static_part + str(1)
            # Join existing fabric.
            if 'Already' in join_fabric(module, switch_ip):
                output += ' %s: Already part of fabric %s \n' % (switch,
                                                                 fabric_name)
            else:
                output += ' %s: Joined fabric %s \n' % (switch, fabric_name)

        bgp_nic_ip_count = (switch_index * switch_count * supernet) + 1
        neighbor_ip_count = bgp_nic_ip_count + 1
        bgp_nic_ip = static_part + str(bgp_nic_ip_count) + '/' + subnet
        neighbor_ip = static_part + str(neighbor_ip_count)

        # Create and configure vrouter.
        output += create_and_configure_vrouter(
            module, bgp_nic_ip, neighbor_ip, switch, cluster_list,
            non_clustered_switches)

    return output


def toggle_40g_local(module):
    """
    Method to toggle 40g ports to 10g ports.
    :param module: The Ansible module to fetch input parameters.
    :return: The output messages for assignment.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' lldp-show format local-port no-show-headers '
    local_ports = run_cli(module, cli).split()

    cli = clicopy
    cli += ' port-config-show speed 40g '
    cli += ' format port no-show-headers '
    ports_40g = run_cli(module, cli)
    if len(ports_40g) > 0 and ports_40g != 'Success':
        ports_40g = ports_40g.split()
        ports_to_modify = list(set(ports_40g) - set(local_ports))

        for port in ports_to_modify:
            next_port = str(int(port) + 1)
            cli = clicopy
            cli += ' port-show port %s format bezel-port' % next_port
            cli += ' no-show-headers'
            bezel_port = run_cli(module, cli).split()[0]

            if '.2' in bezel_port:
                end_port = int(port) + 3
                range_port = port + '-' + str(end_port)

                cli = clicopy
                cli += ' port-config-modify port %s ' % port
                cli += ' disable '
                output += 'port ' + port + ' disabled'
                output += run_cli(module, cli)

                cli = clicopy
                cli += ' port-config-modify port %s ' % port
                cli += ' speed 10g '
                output += 'port ' + port + ' converted to 10g'
                output += run_cli(module, cli)

                cli = clicopy
                cli += ' port-config-modify port %s ' % range_port
                cli += ' enable '
                output += 'port range_port ' + range_port + '  enabled'
                output += run_cli(module, cli)

        time.sleep(10)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
            pn_spine_list=dict(required=True, type='list'),
            pn_leaf_list=dict(required=True, type='list'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_current_switch=dict(required=True, type='str'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_ip=dict(required=False, type='str', default='100.1.1.0/24'),
            pn_accept_eula=dict(required=True, type='bool'),
            pn_bgp_redistribute=dict(required=False, type='str',
                                     default='connected'),
            pn_bgp_max_path=dict(required=False, type='str', default='16'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    current_switch = module.params['pn_current_switch']
    message = ''
    global CHANGED_FLAG

    if module.params['pn_accept_eula']:
        # Auto accept EULA
        if 'Setup completed successfully' in auto_accept_eula(module):
            message += ' %s: EULA accepted \n' % current_switch
            CHANGED_FLAG.append(True)
        else:
            message += ' %s: EULA has already been accepted \n' % current_switch

        # Update switch names to match host names from hosts file
        if 'Updated' in update_switch_names(module, current_switch):
            CHANGED_FLAG.append(True)

        # Toggle 40g ports to 10g
        if toggle_40g_local(module):
            message += ' %s: Toggled 40G ports to 10G \n' % current_switch
            CHANGED_FLAG.append(True)
    else:
        message += implement_dci(module)

    # Exit the module and return the required JSON
    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )

if __name__ == '__main__':
    main()

