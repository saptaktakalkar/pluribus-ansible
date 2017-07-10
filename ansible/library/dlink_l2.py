#!/usr/bin/python
""" PN Dlink L2 VRRP """

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
module: dlink_l2
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to configure L2 VRRP setup
description: Virtual Router Redundancy Protocol (VRRP) - Layer 2 Setup
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
    pn_host_ips:
      description:
        - Specify ips of all hosts/switches separated by comma.
      required: True
      type: str
    pn_vrrp_id:
      description:
        - Specify the vrrp id to be assigned.
      required: False
      default: '18'
      type: str
    pn_csv_data:
      description:
        - String containing vrrp data parsed from csv file.
      required: True
      type: str
"""

EXAMPLES = """
- name: Configure L2 VRRP
  dlink_l2:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_spine_list: "{{ groups['spine'] }}"
    pn_leaf_list: "{{ groups['leaf'] }}"
    pn_current_switch: "{{ inventory_hostname }}"
    pn_host_ips: "{{ groups['all'] |
        map('extract', hostvars, ['ansible_host']) | join(',') }}"
    pn_vrrp_id: '18'
    pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
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
            task='Configure L2 VRRP',
            msg='L2 VRRP configuration failed',
            changed=False
        )
    else:
        return None


def create_vrouter_interface(module, switch, ip, vlan_id, vrrp_priority):
    """
    Add vrouter interface and assign IP along with vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which interfaces will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_priority: Priority to be given(110 for active switch).
    :return: String describing if vrouter interface got added or not.
    """
    global CHANGED_FLAG
    output = ''
    new_vip = False
    new_vrrp_ip = False
    vrouter_name = switch + '-vrouter'
    vrrp_id = module.params['pn_vrrp_id']
    ip_count = module.params['pn_spine_list'].index(switch) + 2

    ip_addr = ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    vip = static_ip + '1' + '/' + subnet
    vrrp_ip = static_ip + str(ip_count) + '/' + subnet

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, vrrp_ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli)

    if existing_vrouter is not None:
        existing_vrouter = existing_vrouter.split()
        if vrouter_name not in existing_vrouter:
            new_vip = True

    if new_vip or existing_vrouter is None:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
        cli += ' ip %s vlan %s if data ' % (vrrp_ip, vlan_id)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += 'Added vrouter interface with ip %s on %s\n' % (vrrp_ip,
                                                                  vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s ' % (
        vrouter_name, vrrp_ip, vlan_id
    )
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s ' % (
        vlan_id, vip, eth_port[0]
    )
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli)
    if existing_vrouter is not None:
        existing_vrouter = existing_vrouter.split()
        if vrouter_name not in existing_vrouter:
            new_vrrp_ip = True

    if new_vrrp_ip or existing_vrouter is None:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
        cli += ' ip %s vlan %s if data vrrp-id %s ' % (vip, vlan_id, vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += 'Added vrouter interface with ip %s on %s\n' % (vip,
                                                                  vrouter_name)

    return output


def create_vlan(module, vlan_id):
    """
    Method to create a vlan.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be created.
    :return: String describing if vlan got created or not.
    """
    global CHANGED_FLAG
    output = ''
    new_vlan = False

    cli = pn_cli(module)
    cli += ' vlan-show format id no-show-headers '
    existing_vlans = run_cli(module, cli)

    if existing_vlans is not None:
        existing_vlans = existing_vlans.split()
        if vlan_id not in existing_vlans:
            new_vlan = True

    if new_vlan or existing_vlans is None:
        cli = pn_cli(module)
        cli += ' vlan-create id %s scope fabric ' % vlan_id
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += 'Created vlan with id %s\n' % vlan_id

    return output


def create_vrouter(module, switch, vnet_name):
    """
    Create a hardware vrouter using vrrp id.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vnet_name: Vnet name required for vrouter creation.
    :return: String describing if vrouter got created or not.
    """
    global CHANGED_FLAG
    output = ''
    new_vrouter = False
    vrouter_name = switch + '-vrouter'

    # Check if vrouter already exists
    cli = pn_cli(module)
    cli += ' switch %s ' % switch
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli)

    if existing_vrouter_names is not None:
        existing_vrouter_names = existing_vrouter_names.split()
        if vrouter_name not in existing_vrouter_names:
            new_vrouter = True

    if new_vrouter or existing_vrouter_names is None:
        cli = pn_cli(module)
        cli += ' switch %s ' % switch
        cli += ' vrouter-create name %s vnet %s hw-vrrp-id %s enable ' % (
            vrouter_name, vnet_name, module.params['pn_vrrp_id']
        )
        cli += ' router-type hardware '
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += 'Created vrouter with name %s\n' % vrouter_name

    return output


def create_vlag(module, name, peer_switch, port, peer_port):
    """
    Create virtual link aggregation groups.
    :param module: The Ansible module to fetch input parameters.
    :param name: The name of the vlag to create.
    :param peer_switch: Name of the peer switch.
    :param port: Name of the trunk on local switch.
    :param peer_port: Name of the trunk on peer switch.
    :return: String describing if vlag got created or not.
    """
    output = ''
    new_vlag = False
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch-local vlag-show format switch,peer-switch, no-show-headers '
    vlag_list = run_cli(module, cli)
    if vlag_list is not None:
        vlag_list = vlag_list.split()
        if peer_switch not in vlag_list:
            new_vlag = True

    if new_vlag or vlag_list is None:
        cli = clicopy
        cli += ' switch-local vlag-create name %s port %s ' % (name, port)
        cli += ' peer-switch %s peer-port %s ' % (peer_switch, peer_port)
        cli += ' mode active-active '
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += 'Configured vLag %s\n' % name

    return output


def create_trunk(module, name, ports):
    """
    Method to create a trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param name: The name of the trunk to create.
    :param ports: List of connected ports.
    :return: String describing if trunk got created or not.
    """
    output = ''
    new_trunk = False
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch-local trunk-show format name no-show-headers '
    trunk_list = run_cli(module, cli)
    if trunk_list is not None:
        trunk_list = trunk_list.split()
        if name not in trunk_list:
            new_trunk = True

    if new_trunk or trunk_list is None:
        cli = clicopy
        ports_string = ','.join(ports)
        cli += ' switch-local trunk-create name %s ' % name
        cli += ' ports %s ' % ports_string
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += 'Created trunk %s\n' % name

    return output


def get_ports(module, peer_switch):
    """
    Get the list of ports connected to peer switch.
    :param module: The Ansible module to fetch input parameters.
    :param peer_switch: Name of the connected peer switch.
    :return: List of connected ports if any else None.
    """
    cli = pn_cli(module)
    cli += ' switch-local port-show hostname %s' % peer_switch
    cli += ' format port no-show-headers '
    ports = run_cli(module, cli)
    return ports.split() if ports is not None else None


def create_cluster(module, name, node1, node2):
    """
    Create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: String describing if cluster got created or not.
    """
    output = ''
    new_cluster = False
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch-local cluster-show format name no-show-headers '
    cluster_list = run_cli(module, cli)
    if cluster_list is not None:
        cluster_list = cluster_list.split()
        if name not in cluster_list:
            new_cluster = True

    if new_cluster or cluster_list is None:
            cli = clicopy
            cli += ' switch-local cluster-create name %s ' % name
            cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
            run_cli(module, cli)
            CHANGED_FLAG.append(True)
            output += 'Created %s\n' % name

    return output


def get_fabric_name(module):
    """
    Get fabric name using fabric-info cli command
    :param module: The Ansible module to fetch input parameters.
    :return: Name of the fabric.
    """
    cli = pn_cli(module)
    cli += ' fabric-info format name no-show-headers '
    return run_cli(module, cli).split()[1]


def check_length(name):
    """
    Check if name length is not greater than 59
    :param name: Name whose length needs to check
    :return: First 59 letters if length is greater than 59
    """
    if len(name) > 59:
        name = name[:59]

    return name


def configure_l2_vrrp(module):
    """
    Method to configure l2 vrrp.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing output of configuration.
    """
    output = ''
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    switch = module.params['pn_current_switch']

    is_spine = True if switch in spine_list else False
    fabric_name = get_fabric_name(module)
    vnet_name = fabric_name + '-global'

    cli = pn_cli(module)
    cli += ' fabric-node-show format name no-show-headers '
    fabric_nodes = run_cli(module, cli).split()

    is_cluster = True if len(fabric_nodes) == 2 else False

    # For a cluster switch, configure cluster, trunk and vlag
    if is_cluster:
        new_vlag = False
        cluster_node = None
        for node in fabric_nodes:
            if node != switch:
                cluster_node = node

        if cluster_node is not None:
            cluster_name = fabric_name + '-cluster'
            output += create_cluster(module, cluster_name, switch, cluster_node)

        if is_spine:
            if len(leaf_list) != 0:
                src_ports = []
                leaf_names = ''
                for leaf in leaf_list:
                    ports = get_ports(module, leaf)
                    if ports is not None:
                        src_ports += ports
                        leaf_names += leaf

                src_ports = list(set(src_ports))
                trunk_name = switch + '-to-' + leaf_names + '-trunk'
                trunk_name = check_length(trunk_name)
                output += create_trunk(module, trunk_name, src_ports)

                cluster_node_trunk_name = cluster_node + '-to-' + leaf_names
                cluster_node_trunk_name += '-trunk'
                cluster_node_trunk_name = check_length(cluster_node_trunk_name)

                cli = pn_cli(module)
                cli += ' trunk-show format name no-show-headers '
                existing_trunks = run_cli(module, cli)
                if existing_trunks is not None:
                    existing_trunks = existing_trunks.split()
                    if (trunk_name in existing_trunks and
                            cluster_node_trunk_name in existing_trunks):
                        new_vlag = True

                if new_vlag:
                    vlag_name = switch + '-' + cluster_node
                    vlag_name += '-to-' + leaf_names + '-vlag'
                    vlag_name = check_length(vlag_name)
                    output += create_vlag(module, vlag_name, cluster_node,
                                          trunk_name, cluster_node_trunk_name)
        else:
            if len(spine_list) != 0:
                src_ports = []
                spine_names = ''
                for spine in spine_list:
                    ports = get_ports(module, spine)
                    if ports is not None:
                        src_ports += ports
                        spine_names += spine

                src_ports = list(set(src_ports))
                trunk_name = switch + '-to-' + spine_names + '-trunk'
                trunk_name = check_length(trunk_name)
                output += create_trunk(module, trunk_name, src_ports)

                cluster_node_trunk_name = cluster_node + '-to-' + spine_names
                cluster_node_trunk_name += '-trunk'
                cluster_node_trunk_name = check_length(cluster_node_trunk_name)

                cli = pn_cli(module)
                cli += ' trunk-show format name no-show-headers '
                existing_trunks = run_cli(module, cli)
                if existing_trunks is not None:
                    existing_trunks = existing_trunks.split()
                    if (trunk_name in existing_trunks and
                            cluster_node_trunk_name in existing_trunks):
                        new_vlag = True

                if new_vlag:
                    vlag_name = switch + '-' + cluster_node
                    vlag_name += '-to-' + spine_names + '-vlag'
                    vlag_name = check_length(vlag_name)
                    output += create_vlag(module, vlag_name, cluster_node,
                                          trunk_name, cluster_node_trunk_name)

    # For non clustered spine/leaf
    else:
        if not is_spine:
            if len(spine_list) != 0:
                src_ports = []
                spine_names = ''
                for spine in spine_list:
                    ports = get_ports(module, spine)
                    if ports is not None:
                        src_ports += ports
                        spine_names += spine

                src_ports = list(set(src_ports))
                trunk_name = switch + '-to-' + spine_names + '-trunk'
                trunk_name = check_length(trunk_name)
                output += create_trunk(module, trunk_name, src_ports)
        else:
            if len(leaf_list) != 0:
                src_ports = []
                leaf_names = ''
                for leaf in leaf_list:
                    ports = get_ports(module, leaf)
                    if ports is not None:
                        src_ports += ports
                        leaf_names += leaf

                src_ports = list(set(src_ports))
                trunk_name = switch + '-to-' + leaf_names + '-trunk'
                trunk_name = check_length(trunk_name)
                output += create_trunk(module, trunk_name, src_ports)

    if is_spine:
        output += create_vrouter(module, switch, vnet_name)

        csv_data = module.params['pn_csv_data'].replace(" ", "")
        csv_data_list = csv_data.split('\n')
        for row in csv_data_list:
            if row.startswith('#'):
                continue
            else:
                elements = row.split(',')
                if not is_cluster and len(elements) == 1:
                    vlan_id = elements[0]
                    output += create_vlan(module, vlan_id)
                elif is_cluster and len(elements) == 3:
                    vrrp_ip = elements[0]
                    vlan_id = elements[1]
                    active_switch = elements[2]
                    output += create_vlan(module, vlan_id)
                    vrrp_priority = '110' if switch == active_switch else '109'
                    output += create_vrouter_interface(module, switch, vrrp_ip,
                                                       vlan_id, vrrp_priority)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_spine_list=dict(required=False, type='list', default=[]),
            pn_leaf_list=dict(required=False, type='list', default=[]),
            pn_current_switch=dict(required=False, type='str'),
            pn_host_ips=dict(required=True, type='str'),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    global CHANGED_FLAG
    results = []

    # L2 vrrp setup.
    message = configure_l2_vrrp(module)

    for line in message.splitlines():
        if line:
            results.append({
                'switch': module.params['pn_current_switch'],
                'output': line
            })

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='L2 VRRP configuration succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Configure L2 VRRP'
    )

if __name__ == '__main__':
    main()

