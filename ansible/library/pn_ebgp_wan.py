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


def add_bgp_as(module):
    """
    Method to add bgp_redistribute to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if bgp-redistribute got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    wan_bgp_as = module.params['pn_wan_bgp_as']

    for switch in module.params['pn_wan_switch_list']:
        cli = clicopy
        cli += ' vrouter-show location %s' % switch
        cli += ' format name no-show-headers'
        vrouter = run_cli(module, cli).split()[0]

        cli = clicopy
        cli += ' vrouter-modify name %s bgp-redistribute %s ' % (vrouter,
                                                                 bgp_as)
        if 'Success' in run_cli(module, cli):
            output += ' %s: Added %s BGP_REDISTRIBUTE to %s \n' % (switch,
                                                                   bgp_as,
                                                                   vrouter)
            CHANGED_FLAG.append(True)

    return output


def create_interface(module, switch, ip, port, vrouter):
    """
    Method to create vrouter interface and assign IP to it.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interfaces.
    :param port: l3-port for the interface.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    output = ''
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli

    cli += ' vrouter-interface-show l3-port %s ip %s ' % (port, ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter not in existing_vrouter:
        # Add vrouter interface.
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter
        cli += ' ip ' + ip
        cli += ' l3-port ' + port
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, ip, vrouter
        )

        CHANGED_FLAG.append(True)
    else:
        output += ' %s: Vrouter interface %s already exists on %s \n' % (
            switch, ip, vrouter
        )

    return output


def add_wan_ibgp_interface(module):
    """
    Method to create vrouter interface and add ebgp neighbor for wan switches.
    :param module: The Ansible module to fetch input parameters.
    :return: The output string informing details of vrouter created and
    """
    bgp_as = module.params['pn_wan_bgp_as']
    switch1 = wan_switch_list[0]
    switch2 = wan_switch_list[1]
    output = ''
    cli = clicopy
    cli += ' switch %s port-show hostname %s ' % (switch1, switch2)
    cli += ' format port no-show-headers '
    port_list = run_cli(module, cli).split()

    ip = ip.split('/')[0]
    ip = ip.split('.')
    static_part = ip[0] + '.' + ip[1] + '.' + ip[2] + '.'
    network_count = 0
    subnet = 4

    while len(port_list) > 0 and port_list[0] != 'Success':
        clicopy = cli
        cli += ' vrouter-show location %s format name no-show-headers ' % switch1
        vrouter_switch1 = run_cli(module, cli).split()[0]

        clicopy = cli
        cli += ' vrouter-show location %s format name no-show-headers ' % switch2
        vrouter_switch2 = run_cli(module, cli).split()[0]

        network = network_count * subnet
        lport = port_list[0]
        delete_trunk(module, switch1, lport, switch2)

        network = subnet * network_count
        ip1 = static_part + str(int(network) + 1)
        ip2 = static_part + str(int(network) + 2)

        output += create_interface(module, switch1, ip1, lport, vrouter_switch1)
        port_list.remove(lport)

        cli = clicopy
        cli += ' switch %s port-show port %s ' % (switch1, lport)
        cli += ' format rport no-show-headers '
        rport = run_cli(module, cli)[0]

        delete_trunk(module, switch2, rport, switch1)
        output += create_interface(module, switch2, ip2, rport, vrouter_switch2)

            cli = clicopy
            cli += ' vrouter-bgp-show remote-as ' + bgp_as
            cli += ' neighbor %s format switch no-show-headers ' % (
                ip2)
            already_added = run_cli(module, cli).split()

            if vrouter_switch1 in already_added:
                output += ' %s: ' % switch1
                output += 'BGP Neighbor %s already exists for %s \n' % (
                    ip2, vrouter_switch1
                )
            else:
                cli = clicopy
                cli += ' vrouter-bgp-add vrouter-name ' + vrouter_switch1
                cli += ' neighbor %s remote-as %s ' % (ip2,
                                                       bgp_as)

                if 'Success' in run_cli(module, cli):
                    output += ' %s: Added BGP Neighbor %s for %s \n' % (
                        switch1, ip2, vrouter_switch1
                    )
                    CHANGED_FLAG.append(True)

            cli = clicopy
            cli += ' vrouter-bgp-show remote-as ' + bgp_as
            cli += ' neighbor %s format switch no-show-headers ' % (
                ip1)
            already_added = run_cli(module, cli).split()

            if vrouter_switch2 in already_added:
                output += ' %s: ' % switch2
                output += 'BGP Neighbor %s already exists for %s \n' % (
                    ip1, vrouter_switch2
                )
            else:
                cli = clicopy
                cli += ' vrouter-bgp-add vrouter-name ' + vrouter_switch2
                cli += ' neighbor %s remote-as %s ' % (ip1,
                                                       bgp_as)

                if 'Success' in run_cli(module, cli):
                    output += ' %s: Added BGP Neighbor %s for %s \n' % (
                        switch2, ip1, vrouter_switch2
                    )
                    CHANGED_FLAG.append(True)

        network += 1
    return output


def configure_ospf_bfd(module, vrouter, ip):
    """
    Method to add ospf_bfd to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter: The vrouter name to add ospf bfd.
    :param ip: The interface ip to associate the ospf bfd.
    :return: String describing if OSPF BFD got added or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vrouter-name %s' % vrouter
    cli += ' ip %s format nic no-show-headers ' % ip
    nic_interface = run_cli(module, cli).split()
    nic_interface = list(set(nic_interface))
    nic_interface.remove(vrouter)

    cli = clicopy
    cli += ' vrouter-interface-config-show vrouter-name %s' % vrouter
    cli += ' nic %s format ospf-bfd no-show-headers ' % nic_interface[0]
    ospf_status = run_cli(module, cli).split()
    ospf_status = list(set(ospf_status))

    cli = clicopy
    cli += ' vrouter-show name ' + vrouter
    cli += ' format location no-show-headers '
    switch = run_cli(module, cli).split()[0]

    if ospf_status[0] != 'Success':
        ospf_status.remove(vrouter)

    if ospf_status[0] != 'enable':
        cli = clicopy
        cli += ' vrouter-interface-config-add vrouter-name %s' % vrouter
        cli += ' nic %s ospf-bfd enable' % nic_interface[0]
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Added OSPF BFD to %s \n' % (switch, vrouter)
    else:
        return ' %s: OSPF BFD already exists for %s \n' % (switch, vrouter)


def add_ospf_neighbor(module):
    """
    Method to add ospf_neighbor to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if ospf neighbors got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    area_id = module.params['pn_ospf_area_id']
    leaf_list = module.params['pn_leaf_list']

    for spine in module.params['pn_spine_list']:
        cli = clicopy
        cli += ' vrouter-show location %s' % spine
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

            host_pos = leaf_list.index(hostname)
            ospf_area_id = str(int(area_id) + int(host_pos) + 1)

            cli = clicopy
            cli += ' vrouter-show location %s' % hostname
            cli += ' format name no-show-headers'
            vrouter_hostname = run_cli(module, cli).split()[0]

            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s l3-port %s' % (
                vrouter_spine, port
            )
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
            ospf_network = static_part + str(ospf_last_octet) + '/' + netmask

            leaf_last_octet = int(last_octet[0]) - 1
            ip_leaf = static_part + str(leaf_last_octet)
            ip_spine = static_part + last_octet[0]

            cli = clicopy
            cli += ' vrouter-ospf-show'
            cli += ' network %s format switch no-show-headers ' % ospf_network
            already_added = run_cli(module, cli).split()

            if vrouter_spine in already_added:
                output += ' %s: OSPF Neighbor already exists for %s \n' % (
                    spine, vrouter_spine
                )
            else:
                if module.params['pn_bfd']:
                    output += configure_ospf_bfd(module, vrouter_spine,
                                                 ip_spine)

                cli = clicopy
                cli += ' vrouter-ospf-add vrouter-name ' + vrouter_spine
                cli += ' network %s ospf-area %s' % (ospf_network,
                                                     ospf_area_id)

                if 'Success' in run_cli(module, cli):
                    output += ' %s: Added OSPF neighbor to %s \n' % (
                        spine, vrouter_spine
                    )
                    CHANGED_FLAG.append(True)

            if vrouter_hostname in already_added:
                output += ' %s: OSPF Neighbor already exists for %s \n' % (
                    hostname, vrouter_hostname
                )
            else:
                if module.params['pn_bfd']:
                    output += configure_ospf_bfd(module, vrouter_hostname,
                                                 ip_leaf)

                cli = clicopy
                cli += ' vrouter-ospf-add vrouter-name ' + vrouter_hostname
                cli += ' network %s ospf-area %s' % (ospf_network,
                                                     ospf_area_id)

                if 'Success' in run_cli(module, cli):
                    output += ' %s: Added OSPF neighbor to %s \n' % (
                        hostname, vrouter_hostname
                    )
                    CHANGED_FLAG.append(True)

    return output


def add_ospf_redistribute(module, vrouter_names):
    """
    Method to add ospf_redistribute to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter_names: List of vrouter names.
    :return: String describing if ospf-redistribute got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s' % vrouter
        cli += ' ospf-redistribute static,connected'
        if 'Success' in run_cli(module, cli):
            cli = clicopy
            cli += ' vrouter-show name ' + vrouter
            cli += ' format location no-show-headers '
            switch = run_cli(module, cli).split()[0]

            output += ' %s: Added OSPF_REDISTRIBUTE to %s \n' % (switch,
                                                                 vrouter)
            CHANGED_FLAG.append(True)

    return output


def vrouter_leafcluster_ospf_add(module, switch_name, interface_ip,
                                 ospf_network):
    """
    Method to create interfaces and add ospf neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: The name of the switch to run interface.
    :param interface_ip: Interface ip to create a vrouter interface.
    :param ospf_network: Ospf network for the ospf neighbor.
    :return: String describing if ospf neighbors got added or not.
    """
    global CHANGED_FLAG
    output = ''
    vlan_id = module.params['pn_iospf_vlan']
    ospf_area_id = module.params['pn_ospf_area_id']

    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s vlan-show format id no-show-headers ' % switch_name
    existing_vlans = run_cli(module, cli).split()

    if vlan_id not in existing_vlans:
        cli = clicopy
        cli += ' switch %s vlan-create id %s scope local ' % (switch_name,
                                                              vlan_id)
        run_cli(module, cli)
        output = ' %s: Vlan with id %s created successfully \n' % (switch_name,
                                                                   vlan_id)
        CHANGED_FLAG.append(True)

    cli = clicopy
    cli += ' vrouter-show location %s format name' % switch_name
    cli += ' no-show-headers'
    vrouter = run_cli(module, cli).split()[0]

    cli = clicopy
    cli += ' vrouter-interface-show ip %s vlan %s' % (interface_ip, vlan_id)
    cli += ' format switch no-show-headers'
    existing_vrouter_interface = run_cli(module, cli).split()

    if vrouter not in existing_vrouter_interface:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name %s ip %s vlan %s ' % (
            vrouter, interface_ip, vlan_id
        )
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch_name, interface_ip, vrouter
        )
        CHANGED_FLAG.append(True)
    else:
        output += ' %s: Vrouter interface %s already exists for %s \n' % (
            switch_name, interface_ip, vrouter
        )

    cli = clicopy
    cli += ' vrouter-ospf-show'
    cli += ' network %s format switch no-show-headers ' % ospf_network
    already_added = run_cli(module, cli).split()

    if vrouter in already_added:
        output += ' %s: OSPF Neighbor already exists for %s \n' % (switch_name,
                                                                   vrouter)
    else:
        cli = clicopy
        cli += ' vrouter-ospf-add vrouter-name ' + vrouter
        cli += ' network %s ospf-area %s' % (ospf_network, ospf_area_id)

        if 'Success' in run_cli(module, cli):
            output += ' %s: Added OSPF neighbor to %s \n' % (switch_name,
                                                             vrouter)
            CHANGED_FLAG.append(True)

    return output


def assign_leafcluster_ospf_interface(module):
    """
    Method to create interfaces and add ospf neighbor for leaf cluster.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of vrouter_interface_ibgp_add() method.
    """
    output = ''
    iospf_ip_range = module.params['pn_iospf_ip_range']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    subnet_count = 0

    cli = pn_cli(module)
    clicopy = cli

    address = iospf_ip_range.split('.')
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
                ospf_network = static_part + str(ip_count) + '/' + str(30)

                cli = clicopy
                cli += ' cluster-show name %s format cluster-node-2' % cluster
                cli += ' no-show-headers'
                cluster_node_2 = run_cli(module, cli).split()[0]

                output += vrouter_leafcluster_ospf_add(module, cluster_node_1,
                                                       ip1, ospf_network)
                output += vrouter_leafcluster_ospf_add(module, cluster_node_2,
                                                       ip2, ospf_network)

                subnet_count += 1
    else:
        output += ' No leaf clusters present to add iOSPF \n'

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
            pn_iospf_vlan=dict(required=False, type='str', default='4040'),
            pn_iospf_ip_range=dict(required=False, type='str',
                                   default='75.75.75.0/30'),
            pn_ospf_area_id=dict(required=False, type='str', default='0'),
            pn_routing_protocol=dict(required=False, type='str',
                                     choices=['ebgp', 'ospf'], default='ebgp'),
        )
    )

    global CHANGED_FLAG
    routing_protocol = module.params['pn_routing_protocol']

    # Get the list of vrouter names.
    cli = pn_cli(module)
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    message = assign_router_id(module, vrouter_names)
    message += create_leaf_clusters(module)

    if routing_protocol == 'ebgp':
        message += assign_bgp_as(module, module.params['pn_bgp_as_range'],
                                 vrouter_names)
        message += add_bgp_redistribute(module,
                                        module.params['pn_bgp_redistribute'],
                                        vrouter_names)
        message += add_bgp_maxpath(module, module.params['pn_bgp_maxpath'],
                                   vrouter_names)
        message += add_bgp_neighbor(module)
        message += assign_wan_bgp_interface(module)
    elif routing_protocol == 'ospf':
        message += add_ospf_neighbor(module)
        message += add_ospf_redistribute(module, vrouter_names)
        message += assign_leafcluster_ospf_interface(module)

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

