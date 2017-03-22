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


def assign_inband_ip(module):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if in-band ip got assigned or not.
    """
    global CHANGED_FLAG
    supernet = 4
    inband_ip = module.params['pn_inband_ip']
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
        CHANGED_FLAG.append(True)
        return '%s: In-band ip assigned with ip %s \n' % (current_switch, ip)

    return ''


def configure_fabric(module, switch):
    """
    Method to configure (create/join) fabric.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the current switch.
    :return: String describing fabric creation/joining description.
    """
    global CHANGED_FLAG
    output = ''
    fabric_name = module.params['pn_fabric_name']
    switch_index = module.params['pn_leaf_list'].index(switch)

    address = module.params['pn_inband_ip'].split('.')
    inband_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    inband_static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    if switch_index == 0:
        cli = pn_cli(module)
        clicopy = cli
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
                                           subnet, switch)
    else:
        switch_ip = inband_static_part + str(1)
        # Join existing fabric.
        if 'Already' in join_fabric(module, switch_ip):
            output += ' %s: Already part of fabric %s \n' % (switch,
                                                             fabric_name)
        else:
            output += ' %s: Joined fabric %s \n' % (switch, fabric_name)
            CHANGED_FLAG.append(True)

    return output


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


def fabric_inband_net_create(module, inband_static_part, subnet, switch):
    """
    Method to create fabric in-band network.
    :param module: The Ansible module to fetch input parameters.
    :param inband_static_part: In-band ip address till third octet.
    :param subnet: Subnet mask of in-band ip address.
    :param switch: Name of the 1st switch in the DC.
    :return: String describing if fabric in-band network got created or not.
    """
    global CHANGED_FLAG
    output = ''
    supernet = 4
    switch_count = 0
    cli = pn_cli(module)
    clicopy = cli

    while switch_count < len(module.params['pn_leaf_list']):
        ip_count = (switch_count * supernet) + 1
        inband_network_ip = inband_static_part + str(ip_count) + '/' + subnet

        cli = clicopy
        cli += 'fabric-in-band-network-show format network no-show-headers'
        existing_networks = run_cli(module, cli).split()

        if inband_network_ip not in existing_networks:
            cli = clicopy
            cli += 'fabric-in-band-network-create network ' + inband_network_ip
            if 'Success' in run_cli(module, cli):
                output += ' %s: Fabric in-band network created for %s \n' % (
                    switch, inband_network_ip
                )
                CHANGED_FLAG.append(True)
        else:
            output += ' %s: Fabric in-band network %s already exists\n' % (
                switch, inband_network_ip
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


def create_vrouter(module, switch, bgp_as, router_id, bgp_nic_ip,
                   bgp_nic_l3_port, neighbor_ip, remote_as, in_band_nic_ip,
                   in_band_nic_netmask, fabric_network_address):
    """
    Method to create vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the current switch.
    :param bgp_as: BGP AS value of this switch.
    :param router_id: Router id to be assigned to this vrouter.
    :param bgp_nic_ip: Bgp_nic_ip for the vrouter creation.
    :param bgp_nic_l3_port: L3 port number connected to neighbor switch.
    :param neighbor_ip: Ip of the BGP neighbor node.
    :param remote_as: BGP AS value of the neighbor node.
    :param in_band_nic_ip: In-band nic ip of this switch.
    :param in_band_nic_netmask: Netmask of in-band nic ip.
    :param fabric_network_address: Fabric network address of the existing fabric
    :return: String describing if vrouter got created or if it already exists.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    clicopy = cli

    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += ' fabric-comm-vrouter-bgp-create name %s ' % vrouter_name
        cli += ' bgp-as %s router-id %s ' % (bgp_as, router_id)
        cli += ' bgp-nic-ip %s ' % bgp_nic_ip
        cli += ' bgp-nic-l3-port %s ' % bgp_nic_l3_port
        cli += ' neighbor %s remote-as %s ' % (neighbor_ip, remote_as)
        cli += ' bfd in-band-nic-ip %s ' % in_band_nic_ip
        cli += ' in-band-nic-netmask %s ' % in_band_nic_netmask

        if fabric_network_address is not None:
            cli += ' fabric-network %s ' % fabric_network_address

        cli += ' allowas-in '
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Created %s \n' % (switch, vrouter_name)
    else:
        return ' %s: %s already exists\n' % (switch, vrouter_name)


def get_l3_port(module, neighbor_name):
    """
    Method to get l3 port number which is connected to given neighbor.
    :param module: The Ansible module to fetch input parameters.
    :param neighbor_name: Name of the bgp neighbor host.
    :return: l3 port number.
    """
    cli = pn_cli(module)
    cli += 'port-show hostname %s format port no-show-headers' % (
        neighbor_name
    )
    ports = run_cli(module, cli).split()

    cli = pn_cli(module)
    cli += 'trunk-show ports %s format trunk-id no-show-headers ' % (
        ports[0]
    )
    trunk_id = run_cli(module, cli)

    if len(trunk_id) == 0 or trunk_id == 'Success':
        return ports[0]
    else:
        return trunk_id


def configure_loopback_interface(module, switch, router_id):
    """
    Method to configure looack interface on a vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param router_id: Router id which is same as loopback ip.
    :return: String describing if loopback interface got configured or not
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    cli += ' vrouter-loopback-interface-add vrouter-name %s ' % vrouter_name
    cli += ' ip %s index 1 ' % router_id
    run_cli(module, cli)

    cli = pn_cli(module)
    cli += ' vrouter-bgp-network-add vrouter-name %s ' % vrouter_name
    cli += ' network %s netmask 255.255.255.255 ' % router_id
    run_cli(module, cli)

    CHANGED_FLAG.append(True)
    return ' %s: Configured loopback interface with ip %s \n' % (switch,
                                                                 router_id)


def configure_ebgp_connections(module, switch, third_party_data, bgp_nic_ip):
    """
    Method to configure eBGP connection to remaining third party neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param third_party_data: Third party BGP data in csv format.
    :param bgp_nic_ip: Ip of first bgp neighbor added.
    :return: String describing eBGP configuration.
    """
    global CHANGED_FLAG
    output = ''
    vrouter_name = switch + '-vrouter'
    skip_flag = False
    address = bgp_nic_ip.split('.')
    bgp_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    bgp_static_part += str(address[2]) + '.'
    bgp_last_octet = str(address[3]).split('/')
    bgp_count = int(bgp_last_octet[0])
    bgp_subnet = bgp_last_octet[1]

    for row in third_party_data:
        row = row.split(',')
        if not skip_flag and row[3] == switch:
            skip_flag = True
            continue

        if skip_flag and row[3] == switch:
            neighbor_name = row[0]
            neighbor_ip = row[1]
            remote_as = row[2]

            l3_port = get_l3_port(module, neighbor_name)
            bgp_count += 1
            ip = bgp_static_part + str(bgp_count) + '/' + bgp_subnet

            cli = pn_cli(module)
            clicopy = cli
            cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
            cli += ' l3-port %s ip %s ' % (l3_port, ip)
            run_cli(module, cli)
            output += ' %s: Added vrouter interface %s \n' % (switch, ip)

            cli = clicopy
            cli += ' vrouter-bgp-add vrouter-name %s ' % vrouter_name
            cli += ' neighbor %s remote-as %s bfd ' % (neighbor_ip, remote_as)
            cli += ' allowas-in '
            run_cli(module, cli)
            output += ' %s: Added eBGP neighbor %s \n' % (switch, neighbor_ip)

            cli = clicopy
            cli += ' vrouter-modify name %s ' % vrouter_name
            cli += ' bgp-max-paths %s ' % module.params['pn_bgp_max_path']
            cli += ' bgp-bestpath-as-path multipath-relax '
            run_cli(module, cli)

    return output


def create_vlan(module, switch):
    """
    Method to create local vlan.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :return: String describing vlan creation details.
    """
    global CHANGED_FLAG
    vlan_id = module.params['pn_ibgp_vlan']
    
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s vlan-show format id no-show-headers ' % switch
    existing_vlan_ids = run_cli(module, cli).split()
    existing_vlan_ids = list(set(existing_vlan_ids))

    if vlan_id not in existing_vlan_ids:
        cli = clicopy
        cli += ' switch %s vlan-create id %s scope local ' % (switch, vlan_id)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        
        cli = clicopy
        cli += ' vlan-port-add vlan-id %s ports 128 tagged ' % vlan_id
        run_cli(module, cli)
        
        return ' %s: Vlan id %s with scope local created \n' % (
            switch, vlan_id
        )

    else:
        return ' %s: Vlan id %s with scope local already exists \n' % (
            switch, vlan_id
        )
    
    
def configure_ibgp_connection(module, switch, local_ip, remote_ip, remote_as):
    """
    Method to configure iBGP connection between cluster members.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param local_ip: Vrouter interface ip of local switch.
    :param remote_ip: Vrouter interface ip of remote switch.
    :param remote_as: Remote-as value of cluster.
    :return: String describing details of iBGP configuration made.
    """
    global CHANGED_FLAG
    output = ''
    vrouter_name = switch + '-vrouter'
    vlan_id = module.params['pn_ibgp_vlan']
    cli = pn_cli(module)
    clicopy = cli
    
    cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
    cli += ' ip %s vlan %s ' % (local_ip, vlan_id)
    run_cli(module, cli)

    output += ' %s: Added vrouter interface with ip %s on %s \n' % (
        switch, local_ip, vrouter_name
    )

    remote_ip = remote_ip.split('/')[0]
    cli = clicopy
    cli += ' vrouter-bgp-add vrouter-name %s ' % vrouter_name
    cli += ' neighbor %s remote-as %s next-hop-self bfd ' % (remote_ip, 
                                                             remote_as)
    run_cli(module, cli)

    output += ' %s: Added iBGP neighbor %s for %s \n' % (switch, remote_ip,
                                                         vrouter_name)

    CHANGED_FLAG.append(True)
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
    bgp_ip = module.params['pn_bgp_ip']
    leaf_list = module.params['pn_leaf_list']
    loopback_ip = module.params['pn_loopback_ip']
    bgp_as_range = module.params['pn_bgp_as_range']
    third_party_data = module.params['pn_third_party_data'].replace(' ', '')
    third_party_data = third_party_data.split('\n')

    address = bgp_ip.split('.')
    bgp_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    bgp_static_part += str(address[2]) + '.'
    bgp_last_octet = str(address[3]).split('/')
    bgp_subnet = bgp_last_octet[1]

    address = loopback_ip.split('.')
    loopback_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    loopback_static_part += str(address[2]) + '.'

    cluster_dict_info = find_clustered_switches(module)
    cluster_list = cluster_dict_info[0]
    cluster_switches = cluster_dict_info[1]
    cluster_list = sorted(cluster_list)
    non_clustered_switches = list(sorted(set(leaf_list) - set(
        cluster_switches)))

    # Calculate bgp-as value for all DC switches.
    bgp_as_dict = {}
    for switch in leaf_list:
        if switch not in bgp_as_dict.keys():
            if switch in non_clustered_switches:
                bgp_as_dict[switch] = bgp_as_range
            else:
                bgp_as_dict[switch] = bgp_as_range
                for cluster in cluster_list:
                    if cluster[0] == switch:
                        bgp_as_dict[cluster[1]] = bgp_as_range
                        break
                    elif cluster[1] == switch:
                        bgp_as_dict[cluster[0]] = bgp_as_range
                        break

            bgp_as_range += supernet

    for switch in leaf_list:
        switch_index = leaf_list.index(switch)
        # Calculate router-id to be assigned to vrouter.
        router_id = loopback_static_part + str(switch_index + 1)

        # Calculate bgp-nic-ip to be assigned while vrouter creation.
        bgp_nic_ip_count = (switch_index * supernet) + 1
        bgp_nic_ip = bgp_static_part + str(bgp_nic_ip_count) + '/' + bgp_subnet

        # Calculate in-band-nic-ip and in-band-nic-netmask for vrouter creation.
        cli = pn_cli(module)
        cli += 'switch-setup-show format in-band-ip no-show-headers'
        inband_ip = run_cli(module, cli)
        address = inband_ip.split(':')[1]
        address = address.replace(' ', '')
        address = address.split('.')
        inband_static_part = str(address[0]) + '.' + str(address[1]) + '.'
        inband_static_part += str(address[2]) + '.'
        inband_last_octet = str(address[3]).split('/')
        inband_nic_ip = inband_static_part + str(int(inband_last_octet[0]) + 1)
        inband_nic_netmask = inband_last_octet[1]

        # Get the bgp-as value
        bgp_as = bgp_as_dict[switch]

        # Get the neighbor ip and remote-as value of the first neighbor
        neighbor_name, neighbor_ip, remote_as = None, None, None
        for row in third_party_data:
            row = row.split(',')
            if row[3] == switch:
                neighbor_name = row[0]
                neighbor_ip = row[1]
                remote_as = row[2]
                break

        if neighbor_name is None or neighbor_ip is None or remote_as is None:
            return ' %s: Could not find remote bgp data \n' % switch

        # Calculate bgp-nic-l3-port number connected to first neighbor
        bgp_nic_l3_port = get_l3_port(module, neighbor_name)

        # Calculate fabric-network address
        if switch_index != 0:
            fabric_network_address = inband_static_part + str(0) + '/'
            fabric_network_address += inband_nic_netmask
        else:
            fabric_network_address = None

        # Create and configure vrouter on this switch.
        output += create_vrouter(module, switch, bgp_as, router_id,
                                 bgp_nic_ip, bgp_nic_l3_port, neighbor_ip,
                                 remote_as, inband_nic_ip, inband_nic_netmask,
                                 fabric_network_address)

        # Configure other eBGP connection to third party switches
        output += configure_ebgp_connections(module, switch, third_party_data,
                                             bgp_nic_ip)

        # Configure loopback interface for debugging purpose.
        output += configure_loopback_interface(module, switch, router_id)

    # Configure iBGP connection between clusters
    for cluster in cluster_list:
        cluster_node1 = cluster[0]
        cluster_node2 = cluster[1]
        
        # Create local vlans on both cluster nodes.
        output += create_vlan(module, cluster_node1)
        output += create_vlan(module, cluster_node2)

        ibgp_ip_range = module.params['pn_ibgp_ip_range']
        subnet_count = 0

        address = ibgp_ip_range.split('.')
        static_part = str(address[0]) + '.' + str(address[1]) + '.'
        static_part += str(address[2]) + '.'
        last_octet = str(address[3]).split('/')
        subnet = last_octet[1]

        ip_count = subnet_count * 4
        node1_ip = static_part + str(ip_count + 1) + '/' + subnet
        node2_ip = static_part + str(ip_count + 2) + '/' + subnet
        subnet_count += 1
    
        # Configure iBGP connection.
        output += configure_ibgp_connection(module, cluster_node1, node1_ip,
                                            node2_ip, 
                                            bgp_as_dict[cluster_node1])
        
        output += configure_ibgp_connection(module, cluster_node2, node2_ip,
                                            node1_ip,
                                            bgp_as_dict[cluster_node1])

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
            pn_fabric_name=dict(required=False, type='str'),
            pn_spine_list=dict(required=True, type='list'),
            pn_leaf_list=dict(required=True, type='list'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_loopback_ip=dict(required=False, type='str',
                                default='109.109.109.0/24'),
            pn_current_switch=dict(required=False, type='str'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_ip=dict(required=False, type='str', default='100.1.1.0/24'),
            pn_accept_eula=dict(required=True, type='bool'),
            pn_bgp_redistribute=dict(required=False, type='str',
                                     default='connected'),
            pn_bgp_max_path=dict(required=False, type='str', default='16'),
            pn_ibgp_vlan=dict(required=False, type='str', default='4040'),
            pn_ibgp_ip_range=dict(required=False, type='str',
                                  default='75.75.75.0/30'),
            pn_csv_data=dict(required=False, type='str'),
            pn_third_party_bgp_data=dict(required=False, type='str'),
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

        # Assign in-band ip
        message += assign_inband_ip(module)

        # Configure fabric
        message += configure_fabric(module, current_switch)
    else:
        # Implement Data Center Interconnect
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

