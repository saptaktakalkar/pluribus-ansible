#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) with EBGP/OSPF"""

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

DOCUMENTATION = """
---
module: pn_ebgp_ospf
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: CLI command to do zero touch provisioning with ebgp.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        EBGP:
          - Assigning bgp_as
          - Configuring bgp_redistribute
          - Configuring bgp_maxpath
          - Assign ebgp_neighbor
          - Assign router_id
          - Create leaf_cluster
          - Add iBGP neighbor for clustered leaf
        OSPF:
          - Assign ospf_neighbor
          - Assign ospf_redistribute
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
    pn_routing_protocol:
      description:
        - Specify which routing protocol to specify.
      required: False
      type: str
      choices: ['ebgp', 'ospf']
    pn_ibgp_ip_range:
      description:
        - Specify ip range for ibgp interface.
      required: False
      type: str
      default: '75.75.75.0/30'
    pn_ibgp_vlan:
      description:
        - Specify vlan for ibgp interface.
      required: False
      type: str
      default: '4040'
    pn_bfd:
      description:
        - Specify bfd flag for the ebgp neighbor.
      required: False
      type: bool
      default: False
    pn_ospf_area_id:
      description:
        - Specify area_id value to be added to vrouter for ospf.
      required: False
      type: str
      default: '0'
"""

EXAMPLES = """
    - name: Configure eBGP/OSPF
      pn_ebgp_ospf:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_spine_list: "{{ groups['spine'] }}"
        pn_leaf_list: "{{ groups['leaf'] }}"
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


def assign_bgp_as(module, bgp_spine):
    """
    Method to assign bgp_as to vrouters.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_spine: The user_input for the bgp_as to be assigned.
    :return: String describing if bgp_as got added to vrouters or not.
    """
    global CHANGED_FLAG
    output = ''
    bgp_leaf = int(bgp_spine) + 1
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    modified_vrouters = []

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-show name ' + vrouter
            cli += ' format location no-show-headers '
            switch_name = run_cli(module, cli).split()[0]
            if switch_name in spine_list:
                cli = clicopy
                cli += ' vrouter-modify name %s bgp-as %s ' % (vrouter,
                                                               bgp_spine)

                if 'Success' in run_cli(module, cli):
                    output += ' Added %s BGP_AS to %s! ' % (bgp_spine, vrouter)
                    CHANGED_FLAG.append(True)

            if switch_name in leaf_list and vrouter not in modified_vrouters:
                cli = clicopy
                cli += ' vrouter-modify name %s bgp-as %s ' % (
                    vrouter, str(bgp_leaf))

                if 'Success' in run_cli(module, cli):
                    output += ' Added %s BGP_AS to %s! ' % (str(bgp_leaf),
                                                            vrouter)
                    CHANGED_FLAG.append(True)
                    modified_vrouters.append(vrouter)

                cli = clicopy
                cli += ' cluster-show format name no-show-headers '
                cluster_list = run_cli(module, cli).split()
                for cluster in cluster_list:
                    if str(switch_name) in str(cluster):
                        cli = clicopy
                        cli += ' cluster-show cluster-node-1 ' + switch_name
                        cli += ' format cluster-node-2 no-show-headers '
                        cluster_node_2 = run_cli(module, cli).split()[0]

                        cli = clicopy
                        cli += ' cluster-show cluster-node-2 ' + switch_name
                        cli += ' format cluster-node-1 no-show-headers '
                        cluster_node_1 = run_cli(module, cli).split()[0]

                        if 'Success' in cluster_node_2:
                            vrouter_name = str(cluster_node_1) + '-vrouter'
                        else:
                            vrouter_name = str(cluster_node_2) + '-vrouter'

                        cli = clicopy
                        cli += ' vrouter-modify name %s bgp-as %s ' % (
                            vrouter_name, str(bgp_leaf))

                        if 'Success' in run_cli(module, cli):
                            output += ' Added %s BGP_AS to %s! ' % (
                                str(bgp_leaf), vrouter_name)
                            CHANGED_FLAG.append(True)
                            modified_vrouters.append(vrouter_name)

                bgp_leaf += 1

    else:
        output += ' No vrouters present/created! '
        CHANGED_FLAG.append(False)

    return output


def vrouter_interface_ibgp_add(module, switch_name, interface_ip, neighbor_ip):
    """
    Method to create interfaces and add ibgp neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: The name of the switch to run interface.
    :param interface_ip: Interface ip to create a vrouter interface.
    :param neighbor_ip: Neighbor_ip for the ibgp neighbor.
    :return: The output of all cli commands.
    """
    global CHANGED_FLAG
    output = ''
    vlan_id = module.params['pn_ibgp_vlan']

    cli = pn_cli(module)
    clicopy = cli

    cli = clicopy
    cli += ' switch %s vlan-show format id no-show-headers ' % switch_name
    existing_vlans = run_cli(module, cli).split()

    if vlan_id not in existing_vlans:
        cli = clicopy
        cli += ' switch %s vlan-create id %s scope local ' % (switch_name,
                                                              vlan_id)
        run_cli(module, cli)
        output = ' vlan with id %s created! ' % vlan_id
        CHANGED_FLAG.append(True)
    else:
        CHANGED_FLAG.append(False)

    cli = clicopy
    cli += ' vrouter-show location %s format name' % switch_name
    cli += ' no-show-headers'
    vrouter = run_cli(module, cli).split()[0]

    cli = clicopy
    cli += ' vrouter-show name %s format bgp-as no-show-headers ' % vrouter
    remote_as = run_cli(module, cli).split()[0]

    cli = clicopy
    cli += ' vrouter-interface-show ip %s vlan %s' % (interface_ip, vlan_id)
    cli += ' format switch no-show-headers'
    existing_vrouter_interface = run_cli(module, cli).split()

    if vrouter not in existing_vrouter_interface:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name %s ip %s vlan %s ' % (
            vrouter, interface_ip, vlan_id)
        run_cli(module, cli)
        output += ' Added vrouter interface with ip %s on %s! ' % (interface_ip,
                                                                   vrouter)
        CHANGED_FLAG.append(True)
    else:
        output += ' Interface already exists on %s! ' % vrouter
        CHANGED_FLAG.append(False)

    neighbor_ip = neighbor_ip.split('/')[0]

    cli = clicopy
    cli += ' vrouter-bgp-show remote-as ' + remote_as
    cli += ' neighbor %s format switch no-show-headers' % neighbor_ip
    already_added = run_cli(module, cli).split()

    if vrouter not in already_added:
        cli = clicopy
        cli += ' vrouter-bgp-add vrouter-name %s' % vrouter
        cli += ' neighbor %s remote-as %s next-hop-self' % (neighbor_ip,
                                                            remote_as)
        run_cli(module, cli)
        output += ' Added iBGP neighbor for %s! ' % vrouter
        CHANGED_FLAG.append(True)
    else:
        output += 'vrouter iBGP neighbour already exists for vrouter %s! ' % (
            vrouter)
        CHANGED_FLAG.append(False)

    return output


def assign_ibgp_interface(module):
    """
    Method to create interfaces and add ibgp neighbors.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of vrouter_interface_ibgp_add() method.
    """
    output = ''
    ibgp_ip_range = module.params['pn_ibgp_ip_range']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    subnet_count = 0

    cli = pn_cli(module)
    clicopy = cli

    address = ibgp_ip_range.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'

    cli += ' cluster-show format name no-show-headers '
    cluster_list = run_cli(module, cli).split()

    if len(cluster_list) > 0 and cluster_list[0] != 'Success':
        for cluster in cluster_list:
            cli = clicopy
            cli += ' cluster-show name %s format cluster-node-1' % cluster
            cli += ' no-show-headers'
            cluster_node_1 = run_cli(module, cli).split()[0]

            if cluster_node_1 not in spine_list and cluster_node_1 in leaf_list:
                ip_count = subnet_count * 4
                ip1 = static_part + str(ip_count + 1) + '/' + str(30)
                ip2 = static_part + str(ip_count + 2) + '/' + str(30)

                cli = clicopy
                cli += ' cluster-show name %s format cluster-node-2' % cluster
                cli += ' no-show-headers'
                cluster_node_2 = run_cli(module, cli).split()[0]

                output += vrouter_interface_ibgp_add(module, cluster_node_1,
                                                     ip1, ip2)
                output += vrouter_interface_ibgp_add(module, cluster_node_2,
                                                     ip2, ip1)

                subnet_count += 1
    else:
        output += 'No leaf clusters present to add iBGP! '

    return output


def add_bgp_neighbor(module):
    """
    Method to add bgp_neighbor to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if bgp neighbors got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-show name %s ' % vrouter
            cli += ' format location no-show-headers '
            switch = run_cli(module, cli).split()[0]

            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s ' % vrouter
            cli += ' format l3-port no-show-headers '
            port_num = run_cli(module, cli).split()
            port_num = list(set(port_num))
            port_num.remove(vrouter)

            for port in port_num:
                cli = clicopy
                cli += ' switch %s port-show port %s ' % (switch, port)
                cli += ' format hostname no-show-headers '
                hostname = run_cli(module, cli).split()[0]

                cli = clicopy
                cli += ' vrouter-show location %s ' % hostname
                cli += ' format bgp-as no-show-headers '
                bgp_hostname = run_cli(module, cli).split()[0]

                cli = clicopy
                cli += ' switch %s port-show port %s ' % (switch, port)
                cli += ' format rport no-show-headers '
                port_hostname = run_cli(module, cli)

                cli = clicopy
                cli += ' vrouter-show location %s ' % hostname
                cli += ' format name no-show-headers '
                vrouter_hostname = run_cli(module, cli).split()[0]

                cli = clicopy
                cli += ' vrouter-interface-show vrouter-name %s ' % (
                    vrouter_hostname)
                cli += ' l3-port %s format ip no-show-headers ' % port_hostname
                ip_hostname_subnet = run_cli(module, cli).split()
                ip_hostname_subnet.remove(vrouter_hostname)

                ip_hostname_subnet = ip_hostname_subnet[0].split('/')
                ip_hostname = ip_hostname_subnet[0]

                cli = clicopy
                cli += ' vrouter-bgp-show remote-as ' + bgp_hostname
                cli += ' neighbor %s format switch no-show-headers ' % (
                    ip_hostname)
                already_added = run_cli(module, cli).split()

                if vrouter in already_added:
                    output += ' BGP Neighbour already added for %s! ' % vrouter
                    CHANGED_FLAG.append(False)
                else:
                    cli = clicopy
                    cli += ' vrouter-bgp-add vrouter-name ' + vrouter
                    cli += ' neighbor %s remote-as %s ' % (ip_hostname,
                                                           bgp_hostname)
                    if module.params['pn_bfd']:
                        cli += ' bfd '

                    leaf_switches = module.params['pn_leaf_list']
                    if switch in leaf_switches:
                        temp_cli = clicopy
                        temp_cli += ' cluster-show format name no-show-headers'
                        cluster_list = run_cli(module, temp_cli).split()
                        for cluster in cluster_list:
                            if switch in cluster:
                                cli += ' weight 100 allowas-in '
                                break

                    if 'Success' in run_cli(module, cli):
                        output += ' Added BGP Neighbour for %s! ' % vrouter
                        CHANGED_FLAG.append(True)

    else:
        print ' No vrouters present/created! '
        CHANGED_FLAG.append(False)

    return output


def assign_router_id(module):
    """
    Method to assign router-id to vrouters which is same as loopback ip.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if router id got assigned or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-loopback-interface-show vrouter-name ' + vrouter
            cli += ' format ip no-show-headers '
            loopback_ip = run_cli(module, cli).split()
            loopback_ip.remove(vrouter)

            cli = clicopy
            cli += ' vrouter-modify name %s router-id %s ' % (vrouter,
                                                              loopback_ip[0])
            if 'Success' in run_cli(module, cli):
                output += ' Added router id %s to %s! ' % (loopback_ip[0],
                                                           vrouter)
                CHANGED_FLAG.append(True)
            else:
                CHANGED_FLAG.append(False)
    else:
        print ' No vrouters present/created! '
        CHANGED_FLAG.append(False)

    return output


def add_bgp_redistribute(module, bgp_redis):
    """
    Method to add bgp_redistribute to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_redis: bgp-redistribute value to add.
    :return: String describing if bgp-redistribute got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s bgp-redistribute %s ' % (vrouter,
                                                                 bgp_redis)
        if 'Success' in run_cli(module, cli):
            output += ' Added %s BGP_REDISTRIBUTE to %s! ' % (bgp_redis,
                                                              vrouter)
            CHANGED_FLAG.append(True)
        else:
            CHANGED_FLAG.append(False)

    return output


def add_bgp_maxpath(module, bgp_max):
    """
    Method to add bgp_maxpath to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_max: bgp-max-paths value to add.
    :return: String describing if bgp-max-paths got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s bgp-max-paths %s ' % (vrouter,
                                                              bgp_max)
        if 'Success' in run_cli(module, cli):
            output += ' Added %s BGP_MAXPATH to %s! ' % (bgp_max, vrouter)
            CHANGED_FLAG.append(True)
        else:
            CHANGED_FLAG.append(False)

    return output


def find_non_clustered_leafs(module):
    """
    Method to find leafs which are not part of any cluster.
    :param module: The Ansible module to fetch input parameters.
    :return: List of non clustered leaf switches.
    """
    non_clustered_leafs = []
    cli = pn_cli(module)
    clicopy = cli
    cli += ' cluster-show format cluster-node-1 no-show-headers '
    cluster1 = run_cli(module, cli).split()

    cli = clicopy
    cli += ' cluster-show format cluster-node-2 no-show-headers '
    cluster2 = run_cli(module, cli).split()

    for leaf in module.params['pn_leaf_list']:
        if (leaf not in cluster1) and (leaf not in cluster2):
            non_clustered_leafs.append(leaf)

    return non_clustered_leafs


def create_cluster(module, switch, name, node1, node2):
    """
    Method to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: The output of run_cli() method.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s created successfully! ' % name
    else:
        CHANGED_FLAG.append(False)
        return ' %s already exists! ' % name


def create_leaf_clusters(module):
    """
    Method to create cluster between two physically connected leaf switches.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of create_cluster() method.
    """
    output = ''
    non_clustered_leafs = find_non_clustered_leafs(module)
    non_clustered_leafs_count = 0
    cli = pn_cli(module)
    clicopy = cli

    while non_clustered_leafs_count == 0:
        if len(non_clustered_leafs) == 0:
            non_clustered_leafs_count += 1
        else:
            node1 = non_clustered_leafs[0]
            non_clustered_leafs.remove(node1)

            cli = clicopy
            cli += ' switch %s lldp-show ' % node1
            cli += ' format sys-name no-show-headers '
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            cli = clicopy
            cli += ' switch %s fabric-node-show ' % node1
            cli += ' format name no-show-headers '
            nodes_in_fabric = run_cli(module, cli).split()
            nodes_in_fabric = list(set(nodes_in_fabric))

            for system in system_names:
                if system not in nodes_in_fabric:
                    system_names.remove(system)

            terminate_flag = 0
            node_count = 0
            while (node_count < len(system_names)) and (terminate_flag == 0):
                node2 = system_names[node_count]
                if node2 in non_clustered_leafs:
                    # Cluster creation
                    cluster_name = node1 + '-to-' + node2 + '-cluster'
                    output += create_cluster(module, node2, cluster_name,
                                             node1, node2)

                    non_clustered_leafs.remove(node2)
                    terminate_flag += 1

                node_count += 1
        return output


def configure_ospf_bfd(module, vrouter, ip):
    """
    This method add ospf_bfd to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter: The vrouter name to add ospf bfd.
    :ip: The interface ip to associate the ospf bfd.
    :return: The output of the adding ospf-neighbor.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s' % vrouter
    cli += ' ip %s format nic no-show-headers ' % ip
    nic_interface = run_cli(module, cli).split()
    nic_interface = list(set(nic_interface))
    nic_interface.remove(vrouter)    

    cli = clicopy
    cli += ' vrouter-interface-config-modify vrouter-name %s' % (
         vrouter)
    cli += ' nic %s ospf-bfd enable' % nic_interface[0]
    if 'Success' in run_cli(module, cli):
        output += ' Added ospf bfd for %s! ' % vrouter

    return output


def configure_ospf_bfd(module, vrouter, ip):
    """
    This method add ospf_bfd to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter: The vrouter name to add ospf bfd.
    :ip: The interface ip to associate the ospf bfd.
    :return: The output of the adding ospf-neighbor.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s' % vrouter
    cli += ' ip %s format nic no-show-headers ' % ip
    nic_interface = run_cli(module, cli).split()
    nic_interface = list(set(nic_interface))
    nic_interface.remove(vrouter)    

    cli = clicopy
    cli += ' vrouter-interface-config-modify vrouter-name %s' % (
         vrouter)
    cli += ' nic %s ospf-bfd enable' % nic_interface[0]
    if 'Success' in run_cli(module, cli):
        output += ' Added ospf bfd for %s! ' % vrouter

    return output


def ospf_neighbor(module):
    """
    Method to add ospf_neighbor to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if ospf neighbors got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    ospf_area_id = module.params['pn_ospf_area_id']
    spine_list = module.params['pn_spine_list']

    if len(spine_list) > 0:
        for spine in spine_list:
            cli = clicopy
            cli += '  vrouter-show location %s' % spine
            cli += ' format name no-show-headers'
            vrouter_spine = run_cli(module, cli).split()[0]

            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s ' % vrouter_spine
            cli += ' format l3-port no-show-headers '
            port_list = run_cli(module, cli).split()
            port_list = list(set(port_list))
            port_list.remove(vrouter_spine)

            for port in port_list:
                cli = clicopy
                cli += ' switch %s port-show port %s' % (spine, port)
                cli += ' format hostname no-show-headers'
                hostname = run_cli(module, cli).split()[0]

                cli = clicopy
                cli += ' vrouter-show location %s' % hostname
                cli += ' format name no-show-headers'
                vrouter_hostname = run_cli(module, cli).split()[0]

                cli = clicopy
                cli += ' vrouter-interface-show vrouter-name %s l3-port %s' % (
                    vrouter_spine, port)
                cli += ' format ip no-show-headers'
                ip = run_cli(module, cli).split()
                ip = list(set(ip))
                ip.remove(vrouter_spine)
                ip = ip[0]

                ip = ip.split('.')
                static_part = str(ip[0]) + '.' + str(ip[1]) + '.'
                static_part += str(ip[2]) + '.'
                last_octet = str(ip[3]).split('/')
                netmask = last_octet[1]

                last_octet_ip_mod = int(last_octet[0]) % 4
                ospf_last_octet = int(last_octet[0]) - last_octet_ip_mod
                ospf_network = static_part + str(
                    ospf_last_octet) + '/' + netmask

                leaf_last_octet = int(last_octet[0]) - 1
                ip_leaf = static_part + str(leaf_last_octet)

                ip_spine = static_part + last_octet[0]

                leaf_last_octet = int(last_octet[0]) - 1
                ip_leaf = static_part + str(leaf_last_octet)

                ip_spine = static_part + last_octet[0]

                cli = clicopy
                cli += ' vrouter-ospf-show'
                cli += ' network %s format switch no-show-headers ' % (
                    ospf_network)
                already_added = run_cli(module, cli).split()

                if vrouter_spine in already_added:
                    output += ' OSPF Neighbour already added for %s! ' % (
                        vrouter_spine)
                    CHANGED_FLAG.append(False)
                else:
                    if module.params['pn_bfd']:
                        output += configure_ospf_bfd(module, vrouter_spine, ip_spine)

                    cli = clicopy
                    cli += ' vrouter-ospf-add vrouter-name ' + vrouter_spine
                    cli += ' network %s ospf-area %s' % (ospf_network,
                                                               ospf_area_id)

                    if 'Success' in run_cli(module, cli):
                        output += ' Added ospf for %s! ' % vrouter_spine
                        CHANGED_FLAG.append(True)

                if vrouter_hostname in already_added:
                    output += ' OSPF Neighbour already added for %s! ' % (
                        vrouter_hostname)
                    CHANGED_FLAG.append(False)
                else:
                    cli = clicopy
                    cli += ' vrouter-ospf-add vrouter-name ' + vrouter_hostname
                    cli += ' network %s ospf-area %s' % (ospf_network,
                                                           ospf_area_id)
                    if module.params['pn_bfd']:
                        output += configure_ospf_bfd(module, vrouter_hostname, ip_leaf)

                    if 'Success' in run_cli(module, cli):
                        output += ' Added ospf for %s! ' % vrouter_hostname
                        CHANGED_FLAG.append(True)

    else:
        CHANGED_FLAG.append(False)

    return output


def add_ospf_redistribute(module):
    """
    Method to add ospf_redistribute to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if ospf-redistribute got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s' % vrouter
        cli += ' ospf-redistribute static,connected'
        if 'Success' in run_cli(module, cli):
            output += ' Added OSPF_REDISTRIBUTE to %s! ' % vrouter
            CHANGED_FLAG.append(True)
        else:
            CHANGED_FLAG.append(False)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_redistribute=dict(required=False, type='str',
                                     choices=['none', 'static', 'connected',
                                              'rip', 'ospf'],
                                     default='connected'),
            pn_bgp_maxpath=dict(required=False, type='str', default='16'),
            pn_bfd=dict(required=False, type='bool', default=False),
            pn_ibgp_ip_range=dict(required=False, type='str',
                                  default='75.75.75.0/30'),
            pn_ibgp_vlan=dict(required=False, type='str', default='4040'),
            pn_ospf_area_id=dict(required=False, type='str', default='0'),
            pn_routing_protocol=dict(required=False, type='str',
                                     choices=['ebgp', 'ospf']),
        )
    )

    global CHANGED_FLAG
    CHANGED_FLAG = []
    routing_protocol = module.params['pn_routing_protocol']

    if routing_protocol == 'ebgp':
        message = create_leaf_clusters(module)
        message += assign_bgp_as(module, module.params['pn_bgp_as_range'])
        message += add_bgp_redistribute(module,
                                        module.params['pn_bgp_redistribute'])
        message += add_bgp_maxpath(module, module.params['pn_bgp_maxpath'])
        message += add_bgp_neighbor(module)
        message += assign_router_id(module)
        message += assign_ibgp_interface(module)
    elif routing_protocol == 'ospf':
        message = add_ospf_neighbor(module)
        message += add_ospf_redistribute(module)
    else:
        message = ' Please use the correct routing protocol! '

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

