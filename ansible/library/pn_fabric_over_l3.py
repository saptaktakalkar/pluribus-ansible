#!/usr/bin/python
""" PN FABRIC OVER LAYER3"""

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

DOCUMENTATION = """
---
module: pn_fabric_over_l3
author: "Pluribus Networks (@gauravbajaj)"
version: 1
short_description: Module to configure fabric over layer3.
description:
     This module allows user to configure switches having inband-ip in different
     subnet so that they can have fabric-wide scope and connections.
     It performs following step:
         - Accepting Eula
         - Changing the switch name to the matching host from hosts file
         - Configure fabric in layer3
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
    pn_eula:
      description:
        - Flag to accept eula
        required: True
        type: bool
"""

EXAMPLES = """
    - name: pn_fabric_over_l3
      pn_fabric_over_l3:
        pn_eula: False
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_fabric_name: 'gauravleo'
        pn_spine_list: "{{ groups['spine'] }}"
        pn_leaf_list: "{{ groups['leaf'] }}"
        pn_current_switch: "{{ inventory_hostname }}"
        pn_inband_ip: '172.16.0.0/24'
        pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"

"""

RETURN = """
    description: The set of responses for each command.
      returned: always
      type: str
    changed:
      description: Indicates whether the CLI caused changes on the target.
      returned: always
      type: bool
"""

def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch.
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
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon
    the response from cli.
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
        return ' EULA has been accepted already! '


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
    :param inband_ip: The network ip for the in-band ips.
    :return: The output messages for assignment.
    """
    cli = pn_cli(module)
    clicopy = cli

    supernet = 4
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    output = ''
    ip_count = 0

    if current_switch in spine_list:
        spine_pos = int(spine_list.index(current_switch))
        ip_count = (supernet * spine_pos) + 1
    elif current_switch in leaf_list:
        spine_count = len(spine_list)
        leaf_pos = int(leaf_list.index(current_switch))
        ip_count = (supernet * leaf_pos) + 1
        ip_count += (int(spine_count) * supernet)

    address = inband_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    # last_octet = str(address[3]).split('/')
    # subnet = last_octet[1]

    ip = static_part + str(ip_count) + '/' + str(30)

    cli = clicopy
    cli += 'switch-setup-modify in-band-ip %s ' % ip
    output += run_cli(module, cli)

    return output


def find_leaf_cluster(module):
    """
    Method to find leaf_cluster from the input csv file.
    :param module: The Ansible module to fetch input parameters.
    :return: It returns a dict whose first value is list of pairs of cluster
             and second is list of leaf in cluster.
    """
    csv_data = module.params['pn_csv_data']

    csv_data = csv_data.split('\n')
    dict_leaf_info = {}
    cluster_count = 0
    cluster_list = []
    cluster_leaf = []

    for line in csv_data:

        if line != '':
            line = line.split(',')
            cluster_1 = line[2]
            cluster_2 = line[3]
            cluster_2 = cluster_2.replace(' ', '')

            if cluster_2 != '':
                temp_list = []
                cluster_1 = cluster_1.replace(' ', '')
                temp_list.append(cluster_1)
                temp_list.append(cluster_2)

                if temp_list not in cluster_list:
                    cluster_leaf.append(cluster_1)
                    cluster_leaf.append(cluster_2)
                    cluster_list.append(temp_list)
                    cluster_count += 1

    dict_leaf_info[0] = cluster_list
    dict_leaf_info[1] = cluster_leaf

    return dict_leaf_info


def fabric_inband_net_create(module, inband_static_part):
    """
    Method to create in-band network.
    :param module: The Ansible module to fetch input parameters.
    :param inband_static_part: It contains ip address of inband ip till third
                               octet.
    :return: The output messages for fabric-in-band-network-create.
    """
    cli = pn_cli(module)
    clicopy = cli

    supernet = 4
    output = ''
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    length_switch = int(len(spine_list)) + int(len(leaf_list))

    switch_num = 0
    while switch_num <= (length_switch - 1):
        ip_count = switch_num * supernet
        inband_network_ip = inband_static_part + str(ip_count) + '/' + '30'

        cli = clicopy
        cli += 'fabric-in-band-network-show format network, no-show-headers'
        existing_networks = run_cli(module, cli).split()

        if inband_network_ip not in existing_networks:
            cli = clicopy
            cli += 'fabric-in-band-network-create network %s' % inband_network_ip
            output += run_cli(module, cli)
        else:
            output += 'Inband network already added '
        switch_num += 1

    return output


def join_fabric(module, switch_ip):
    """
    Method to join a fabric with default fabric type as mgmt.
    :param module: The Ansible module to fetch input parameters.
    :param switch_ip: Inband ip of the originator switch.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    clicopy = cli
    output = ''
    cli = clicopy
    cli += ' fabric-info format name no-show-headers'
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if err:
        cli = clicopy
        cli += 'fabric-join switch-ip %s ' % switch_ip
        output += run_cli(module, cli)
    elif out:
        output += "Already in a fabric "
    return output


def fabric_comm(module, bgp_nic_ip, neighbor_ip, remote_switch, cluster_list,
                non_cluster_leaf):
    """
    Method to run fabric-comm command.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_nic_ip: Bgp_nic_ip for the fabric-comm.
    :param neighbor_ip: Neighbor_ip for the fabric-comm.
    :param remote_switch: Remote switch for the fabric-comm.
    :param cluster_list: Pair of leaf clusters.
    :param non_cluster_leaf: List of non_cluster leaf.
    :return: The output of all cli commands.
    """
    output = ''
    # supernet = 4
    vrouter_name = module.params['pn_current_switch']
    bgp_spine = module.params['pn_bgp_as_range']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    bgp_redistribute = module.params['pn_bgp_redistribute']
    bgp_max_path = module.params['pn_bgp_max_path']
    length_non_cluster_leaf = len(non_cluster_leaf)

    cli = pn_cli(module)
    clicopy = cli

    cli = clicopy
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
            bgp_as = bgp_spine
            if remote_switch in non_cluster_leaf:
                remote_as = int(bgp_spine) + 1 + non_cluster_leaf.index(
                    remote_switch)
            else:
                cluster_count = 0
                stop_flag = 0
                while cluster_count < len(cluster_list) and stop_flag == 0:
                    if remote_switch in cluster_list[cluster_count]:
                        remote_as = int(
                            length_non_cluster_leaf) + 1 + cluster_count + int(
                            bgp_spine)
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

            if current_switch in non_cluster_leaf:
                bgp_as = int(bgp_spine) + 1 + non_cluster_leaf.index(
                    current_switch)
            else:
                cluster_count = 0
                stop_flag = 0
                while cluster_count < len(cluster_list) and stop_flag == 0:
                    if current_switch in cluster_list[cluster_count]:
                        bgp_as = int(
                            length_non_cluster_leaf) + 1 + cluster_count + int(
                            bgp_spine)
                        stop_flag += 1
                    cluster_count += 1
            remote_as = bgp_spine
            bgp_as = str(bgp_as)

            cli = clicopy
            cli += 'port-show hostname %s format port, no-show-headers' % spine_list[0]
            ports = run_cli(module, cli).split()

            cli = clicopy
            cli += 'trunk-show ports %s format trunk-id, no-show-headers ' % ports[0]
            trunk_id = run_cli(module, cli)
            if len(trunk_id) == 0 or trunk_id == 'Success':
                l3_port = ports[0]
            else:
                l3_port = trunk_id

            fabric_network_addr = static_part + str(0) + '/' + netmask

        cli = clicopy
        cli += 'fabric-comm-vrouter-bgp-create name %s bgp-as %s' % (vrouter_name, bgp_as)
        cli += ' bgp-redistribute %s bgp-max-paths %s' % (bgp_redistribute, bgp_max_path)
        cli += ' bgp-nic-ip %s bgp-nic-l3-port %s' % (bgp_nic_ip, l3_port)
        cli += ' neighbor %s remote-as %s' % (neighbor_ip, remote_as)

        if current_switch in spine_list and spine_list.index(current_switch) == 0:
            pass
        else:
            cli += ' fabric-network %s' % fabric_network_addr

        cli += ' in-band-nic-ip %s in-band-nic-netmask %s bfd' % (ip, netmask)
        cli += ' allowas-in'
        output += run_cli(module, cli)

    return output


def add_interface_neighbor(module, interface_ip, neighbor_ip, remote_switch, cluster_list, non_cluster_leaf):
    """
    Method to create interfaces and add ebgp neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param interface_ip: Interface ip to create a vrouter interface.
    :param neighbor_ip: Neighbor_ip for the bgp neighbor.
    :param remote_switch: Remote switch.
    :param cluster_list: Pair of leaf clusters.
    :param non_cluster_leaf: List of non_cluster leaf.
    :return: The output of all cli commands.
    """
    output = ''
    length_non_cluster_leaf = len(non_cluster_leaf)

    cli = pn_cli(module)
    clicopy = cli

    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    bgp_spine = module.params['pn_bgp_as_range']

    cli = clicopy
    cli += 'vrouter-show location %s format name no-show-headers' % current_switch
    vrouter_name = run_cli(module, cli).split()

    cli = clicopy
    cli += 'switch %s port-show hostname %s format port, no-show-headers' % (current_switch, remote_switch)
    ports = run_cli(module, cli).split()

    cli = clicopy
    cli += 'switch %s trunk-show ports %s format trunk-id, no-show-headers ' % (current_switch, ports[0])
    trunk_id = run_cli(module, cli).split()
    if len(trunk_id) == 0 or trunk_id[0] == 'Success':
        l3_port = ports[0]
    else:
        l3_port = trunk_id[0]

    cli = clicopy
    cli += ' switch %s vrouter-interface-show ip %s ' % (current_switch, interface_ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy
        cli += 'vrouter-interface-add vrouter-name %s ' % vrouter_name[0]
        cli += 'ip %s l3-port %s ' % (interface_ip, l3_port)
        output += run_cli(module, cli)

    if current_switch in leaf_list:
        remote_as = bgp_spine
    else:
        if remote_switch in non_cluster_leaf:
            remote_as = int(bgp_spine) + 1 + non_cluster_leaf.index(remote_switch)
        else:
            cluster_count = 0
            stop_flag = 0
            while cluster_count < len(cluster_list) and stop_flag == 0:
                if remote_switch in cluster_list[cluster_count]:
                    remote_as = int(length_non_cluster_leaf) + 1 + cluster_count + int(bgp_spine)
                    stop_flag += 1
                    cluster_count += 1
        remote_as = str(remote_as)

    cli = clicopy
    cli += ' vrouter-bgp-show remote-as ' + remote_as
    cli += ' neighbor %s format switch no-show-headers ' % neighbor_ip
    already_added = run_cli(module, cli).split()

    if vrouter_name[0] in already_added:
        output += ' BGP Neighbour already added for %s! ' % vrouter_name[0]
    else:
        cli = clicopy
        cli += 'vrouter-bgp-add vrouter-name %s ' % vrouter_name[0]
        cli += 'neighbor %s remote-as %s' % (neighbor_ip, remote_as)
        cli += ' allowas-in bfd'
        output += run_cli(module, cli)
    return output


def configure_fabric_over_l3(module):
    """
    Method to configure fabric in layer3.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of all cli commands.
    """
    cli = pn_cli(module)
    clicopy = cli
    supernet = 4
    output = ''
    inband_ip = module.params['pn_inband_ip']
    bgp_ip = module.params['pn_bgp_ip']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    fabric_name = module.params['pn_fabric_name']

    output += assign_inband_ip(module, inband_ip)

    address = bgp_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    # last_octet = str(address[3]).split('/')
    # subnet = last_octet[1]
    leaf_count = len(leaf_list)
    # spine_count = len(spine_list)

    address = inband_ip.split('.')
    inband_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    inband_static_part += str(address[2]) + '.'
    # last_octet = str(address[3]).split('/')
    switch_ip = inband_static_part + str(1)

    dict_leaf_info = find_leaf_cluster(module)
    cluster_leaf = dict_leaf_info[1]
    cluster_list = dict_leaf_info[0]
    cluster_list = sorted(cluster_list)
    non_cluster_leaf = list(sorted(set(leaf_list) - set(cluster_leaf)))

    if current_switch in spine_list:
        for leaf in leaf_list:
            spine_pos = spine_list.index(current_switch)
            if leaf_list.index(leaf) == 0:

                if spine_pos == 0:
                    cli = clicopy
                    cli += 'fabric-show format name, no-show-headers'
                    existing_fabric = run_cli(module, cli).split()

                    if fabric_name not in existing_fabric:
                        cli = clicopy
                        cli += 'fabric-create name %s ' % fabric_name
                        output += run_cli(module, cli)
                    else:
                        output += "Fabric already created"

                bgp_nic_ip_count = (spine_pos * leaf_count * supernet) + 1
                neighbor_ip_count = bgp_nic_ip_count + 1
                bgp_nic_ip = static_part + str(bgp_nic_ip_count) + '/' + str(30)
                neighbor_ip = static_part + str(neighbor_ip_count)
                output += fabric_comm(module, bgp_nic_ip, neighbor_ip, leaf, cluster_list, non_cluster_leaf)

                if spine_pos == 0:
                    output += fabric_inband_net_create(module, inband_static_part)
                else:
                    output += join_fabric(module, switch_ip)

            else:
                leaf_pos = leaf_list.index(leaf)
                interface_ip_count = (supernet * leaf_pos) + 1
                interface_ip_count += (supernet * leaf_count * spine_pos)
                neighbor_ip_count = interface_ip_count + 1
                interface_ip = static_part + str(interface_ip_count) + '/' + str(30)
                neighbor_ip = static_part + str(neighbor_ip_count)
                output += add_interface_neighbor(module, interface_ip, neighbor_ip,
                                                 leaf, cluster_list,
                                                 non_cluster_leaf)

    elif current_switch in leaf_list:
        for spine in spine_list:
            spine_pos = spine_list.index(spine)
            if spine_list.index(spine) == 0:
                leaf_pos = leaf_list.index(current_switch)
                bgp_nic_ip_count = (leaf_pos * supernet) + 2
                neighbor_ip_count = bgp_nic_ip_count - 1
                bgp_nic_ip = static_part + str(bgp_nic_ip_count) + '/' + str(30)
                neighbor_ip = static_part + str(neighbor_ip_count)
                output += fabric_comm(module, bgp_nic_ip, neighbor_ip, spine,
                                      cluster_list, non_cluster_leaf)

                output += join_fabric(module, switch_ip)

            else:
                leaf_pos = leaf_list.index(current_switch)
                interface_ip_count = (leaf_pos * supernet) + 2
                interface_ip_count += (supernet * leaf_count * spine_pos)
                neighbor_ip_count = interface_ip_count - 1
                interface_ip = static_part + str(interface_ip_count) + '/' + str(30)
                neighbor_ip = static_part + str(neighbor_ip_count)
                output += add_interface_neighbor(module, interface_ip, neighbor_ip,
                                                 spine, cluster_list, non_cluster_leaf)

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
            pn_eula=dict(required=True, type='bool'),
            pn_bgp_redistribute=dict(required=False, type='str', default='connected'),
            pn_bgp_max_path=dict(required=False, type='str', default='16'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    current_switch = module.params['pn_current_switch']
    eula_flag = module.params['pn_eula']
    message = ' '

    if eula_flag:
        message += auto_accept_eula(module)
        message += update_switch_names(module, current_switch)
        message += toggle_40g_local(module)
    else:
        message += configure_fabric_over_l3(module)

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True
    )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

