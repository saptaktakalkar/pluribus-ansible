#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) """

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
import time
import shlex
import json
DOCUMENTATION = """
---
module: pn_ztp
author: "Pluribus Networks (@saptaktakalkar)"
modified by: "Pluribus Networks (@gauravbajaj)"
version: 1
short_description: CLI command to do zero touch provisioning.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Accept EULA
        - Disable STP
        - Enable all ports
        - Create/Join fabric
        - For Layer 2 fabric: Auto configure vlags
        - For layer 3 fabric: Auto configure link IPs
        - Change fabric type to in-band
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
    pn_cliswitch:
      description:
        - Target switch(es) to run the CLI on.
      required: False
      type: str
    pn_fabric_name:
      description:
        - Specify name of the fabric.
      required: False
      type: str
    pn_fabric_network:
      description:
        - Specify fabric network type as either mgmt or in-band.
      required: False
      type: str
      choices: ['mgmt', 'in-band']
      default: 'mgmt'
    pn_fabric_type:
      description:
        - Specify fabric type as either layer2 or layer3.
      required: False
      type: str
      choices: ['layer2', 'layer3']
      default: 'layer2'
    pn_run_l2_l3:
      description:
        - Boolean flag to decide whether to configure vlag and link IPs or not.
      required: False
      type: bool
      default: False
    pn_net_address:
      description:
        - Specify network address to be used in configuring link IPs for layer3.
      required: False
      type: str
    pn_cidr:
      description:
        - Specify CIDR value to be used in configuring link IPs for layer3.
      required: False
      type: str
    pn_supernet:
      description:
        - Specify supernet value to be used in configuring link IPs for layer3.
      required: False
      type: str
"""

EXAMPLES = """
- name: Zero Touch Provisioning - Initial setup
  pn_ztp:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_fabric_name: ztp-fabric
    pn_run_l2_l3: False

- name: Zero Touch Provisioning - Layer2/Layer3 setup
  pn_ztp:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_cliswitch: squirtle
    pn_fabric_type: layer3
    pn_run_l2_l3: True
    pn_net_address: '192.168.0.1'
    pn_cidr: '24'
    pn_supernet: '30'
"""

RETURN = """
msg:
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
    :param module: The Ansible module to fetch username, password and switch
    :return: The cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s'  % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch:
        cli += ' switch ' + cliswitch
    #else:
    #    cli += ' switch-local '

    return cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon the response from cli.
    """

    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)
#    print "rc",rc
#    print "out",out
#    print "err",err
    if out:
        return out

    if err:
   
        module.exit_json(

            error="1",
            failed=True,
            stderr=err.strip(),
            msg="Operation Failed: " + str(cli),
            changed=False      
            )
        

    else:
        return 'Success'


#def find_hosts(module):
#    host_file = open('/etc/ansible/pluribus-ansible/ansible/hosts', 'r')
#    host = host_file.read()
#    host_file.close()
#    host = host.split()
#
#    i = 0
#    spine= []
#    leaf = []
#    while i < len(host):
#        if host[i] == '[spine]':
#            i += 1
#            while host[i] != '[leaf]':
#                spine.append(host[i])
#                i += 1
#
#            if host[i] == '[leaf]':
#                i += 1
#                while i < len(host):
#                    leaf.append(host[i])
#                    i += 1
#
#        else:
#            i += 1
#
#    host_dict = {
#        "spine" : spine,
#        "leaf"  : leaf
#    }
#
#
#    return host_dict




def auto_accept_eula(module):
    """
    This method is to accept the EULA when we first login to new switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    password = module.params['pn_clipassword']
    cli = '/usr/bin/cli --quiet '
    cli += ' --skip-setup --script-password switch-setup-modify '
    cli += ' eula-accepted true password ' + password
    return run_cli(module, cli)



def modify_stp(module, modify_flag):
    """
    This method is to enable/disable STP (Spanning Tree Protocol) of a switch.
    :param module: The Ansible module to fetch input parameters.
    :param modify_flag: Enable/disable flag to set.
    :return: The output of run_cli() method.
    """
   
    output = ' '
    cli = pn_cli(module)
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    for switch in switch_names:
        cli = clicopy
        cli += ' switch %s ' % (switch)
        cli += ' stp-modify ' + modify_flag
        output += run_cli(module, cli)
        output += ' '
    return output    
    







def configure_control_network(module, network):
    """
    This method is to convert the fabric control network into management.
    :param module: The Ansible module to fetch input parameters.
    :param network: It can be in-band or management.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' fabric-local-modify control-network ' + network
    return run_cli(module, cli)



def enable_ports(module):
    """
    This method is to enable all ports of a switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    print "inside enable ports"
    cli = pn_cli(module)
    cli += ' port-config-show format port no-show-headers '
    out = run_cli(module, cli)
    cli = pn_cli(module)
    cli += ' port-config-show format port speed 40g no-show-headers'
    out_40g = run_cli(module, cli)
    if out_40g:
        out_remove10g = []
        out_40g = out_40g.split()
        out_40g = list(set(out_40g))
        
        for i in out_40g:
            out_remove10g.append(str(int(i) + int(1)))
            out_remove10g.append(str(int(i) + int(2)))
            out_remove10g.append(str(int(i) + int(3)))
     
    if out:
        out = out.split()
        out = set(out) - set(out_remove10g)
        out = list(out)
        ports = ','.join(out)
        cli = pn_cli(module)
        cli += ' port-config-modify port %s enable ' % ports
        return run_cli(module, cli)
    else:
        return out


def create_fabric(module, fabric_name, fabric_network):
    """
    This method is to create a fabric with default fabric type as mgmt.If not joined, join to the fabric.
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to create.
    :param fabric_network: Type of the fabric to create (mgmt/inband). Default value: mgmt
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cliinfo = cli    
    clicopy = cli

    cli = clicopy
    cli += ' fabric-show format name no-show-headers ' 
    fabrics_names = run_cli(module, cli).split()
    if fabric_name not in fabrics_names:
        cli = clicopy
        cli += ' fabric-create name %s fabric-network %s ' % (fabric_name, fabric_network)
    else:
        cliinfo += ' fabric-info format name no-show-headers'
        cliinfo = shlex.split(cliinfo)
        rc, out, err = module.run_command(cliinfo)
        if err:
            cli = clicopy
            cli += ' fabric-join name ' + fabric_name
        elif out:
            myfabricname = out.split()
            if myfabricname[1] not in fabrics_names:
                cli = clicopy
                cli += ' fabric-join name ' + fabric_name
            else:
                return "Already in the fabric"
    return run_cli(module, cli)


#def join_fabric(module, fabric_name):
#    """
#    This method is for a switch to join already existing fabric.
#    :param module: The Ansible module to fetch input parameters.
#    :param fabric_name: Name of the fabric to join.
#    :return: The output of run_cli() method.
#    """
#    cli = pn_cli(module)
#    cli += ' fabric-join name ' + fabric_name
#    return run_cli(module, cli)


def update_fabric_network_to_inband(module):
    """
    This method is to update fabric network type to in-band
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    output = ' '
    cli = pn_cli(module)
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    for switch in switch_names:
        cli = clicopy
        cli += ' switch %s ' % (switch)
        cli += ' fabric-local-modify fabric-network in-band '
        output += run_cli(module, cli)
    return output


#def calculate_link_ip_addresses(address_str, cidr_str, supernet_str):
#    """
#    This method is to calculate link IPs for layer 3 fabric
#    :param address_str: Host/network address.
#    :param cidr_str: Subnet mask.
#    :param supernet_str: Supernet mask
#    :return: List of available IP addresses that can be assigned to vrouter
#    interfaces for layer 3 fabric.
#    """
#    # Split address into octets and turn CIDR, supernet mask into int
#    address = address_str.split('.')
#    cidr = int(cidr_str)
#    supernet = int(supernet_str)
#    supernet_mapping = {
#        30: 2,
#        29: 6,
#        28: 14,
#        27: 30
#    }
#    supernet_range = supernet_mapping[supernet]
#    base_addr = int(address[3])
#    # Initialize the netmask and calculate based on CIDR mask
#    mask = [0, 0, 0, 0]
#    for i in range(cidr):
#        mask[i / 8] += (1 << (7 - i % 8))
#
#    # Initialize net and binary and netmask with addr to get network
#    network = []
#    for i in range(4):
#        network.append(int(address[i]) & mask[i])
#
#    # Duplicate net into broad array, gather host bits, and generate broadcast
#    broadcast = list(network)
#    broadcast_range = 32 - cidr
#    for i in range(broadcast_range):
#        broadcast[3 - i / 8] += (1 << (i % 8))
#
#    last_ip = list(broadcast)
#    """
#    code modified for valid ip calculation
#    """
#    diff = base_addr % (supernet_range + 2)
#    i = base_addr - diff
#    count, hostmin, hostmax = 0, 0, 0
#    ips_list = []
#
#    while count < last_ip[3]:
#        hostmin = i + 1
#        hostmax = hostmin + supernet_range - 1
#        while hostmin <= hostmax:
##            if  hostmin >= base_addr:
#            ips_list.append(hostmin)
#            hostmin += 1
#
#        i = hostmax + 2
#        count = i
#
#    available_ips = []
#    list_index = 0
#    ip_address = str(last_ip[0]) + '.' + str(last_ip[1]) + '.' + str(last_ip[2])
#    while list_index < len(ips_list):
#        """
#        code changed
#        """
#        # ip = ip_address + '.' + str(ips_list[list_index])
#        ip = ip_address + '.' + str(ips_list[list_index])  + "/" + supernet_str
#        available_ips.append(ip)
#        list_index += 1
#
#    return available_ips



def calculate_link_ip_addresses(address_str, cidr_str, supernet_str):
    """
    This method is to calculate link IPs for layer 3 fabric
    :param address_str: Host/network address.
    :param cidr_str: Subnet mask.
    :param supernet_str: Supernet mask
    :return: List of available IP addresses that can be assigned to vrouter
    interfaces for layer 3 fabric.
    """
    # Split address into octets and turn CIDR, supernet mask into int
    address = address_str.split('.')
    cidr = int(cidr_str)
    supernet = int(supernet_str)
    supernet_mapping = {
        30: 2,
        29: 6,
        28: 14,
        27: 30
    }
    supernet_range = supernet_mapping[supernet]
    base_addr = int(address[3])
    # Initialize the netmask and calculate based on CIDR mask
    mask = [0, 0, 0, 0]
    for i in range(cidr):
        mask[i / 8] += (1 << (7 - i % 8))
    # Initialize net and binary and netmask with addr to get network
    network = []
    for i in range(4):
        network.append(int(address[i]) & mask[i])

    # Duplicate net into broad array, gather host bits, and generate broadcast
    broadcast = list(network)
    broadcast_range = 32 - cidr
    for i in range(broadcast_range):
        broadcast[3 - i / 8] += (1 << (i % 8))
    last_ip = list(broadcast)
    diff = base_addr % (supernet_range + 2)
    i = base_addr - diff
    count, hostmin, hostmax = 0, 0, 0
    third_octet = network[2]
    available_ips = []
    while third_octet <= last_ip[2]:
        ips_list = []
        while count < last_ip[3]:
            hostmin = i + 1
            hostmax = hostmin + supernet_range - 1
            while hostmin <= hostmax:
                ips_list.append(hostmin)
                hostmin += 1
            i = hostmax + 2
            count = i

        list_index = 0
        ip_address = str(last_ip[0]) + '.' + str(last_ip[1]) + '.' + str(third_octet)
        while list_index < len(ips_list):
            ip = ip_address + '.' + str(ips_list[list_index]) + "/" + supernet_str
            available_ips.append(ip)
            list_index += 1
        i, count, hostmax, hostmin = 0, 0, 0, 0
        third_octet += 1

    return available_ips





  





def create_vrouter(module, switch):
    """
    This method is to create vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.   
    :return: The output string informing details of vrouter created 
    if vrouter already exists.
    """
    switch_temp = switch[3:]
    vrouter_name = switch_temp + '-vrouter'
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    cli += ' switch ' + switch
    cli_copy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = cli_copy
        cli += ' vrouter-create name %s vnet %s ' % (vrouter_name, vnet_name)
        run_cli(module, cli)
        output = ' Created vrouter %s on switch %s ' % (vrouter_name, switch)
    else:
        output = ' Vrouter name %s on switch %s already exists. ' % (vrouter_name, switch)

    return output




def create_interface(module, switch, ip, port):
    """
    This method is to create vrouter interface and assign IP to it.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interfaces.
    :param port: l3-port for the interface.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
#    switch_temp = switch[3:]   
#    vrouter_name = switch_temp + '-vrouter'
    output = ' ' 
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    cli += ' vrouter-show location %s format name no-show-headers ' % (switch)
    vrouter_name = run_cli(module, cli).split()

    cli = clicopy
    cli += ' vrouter-interface-show l3-port %s ip %s format switch no-show-headers ' % (port, ip) 
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy 
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip
        cli += ' l3-port ' + port
   
        run_cli(module, cli)

        output += ' and added vrouter interface with ip: ' + ip
    else:
        output += ' already created interface on vrouter %s ' % (vrouter_name[0])

    return output


def disable_trunk(module, switch):
    """
    This method is to disable trunk setting on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    cli += ' switch %s sys-flow-setting-modify no-auto-trunk ' % (switch)
    
    return run_cli(module, cli)



def delete_trunk(module, switch, switch_port, peer_switch):
    """
    This method is to delete a conflicting trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param switch_port: The l3-port which is part of conflicting trunk for l3.
    :param peer-switch: The port connecting the switch to another switch. This 
     switch is peer_switch
    :return: The output of run_cli() method.
    """
    output = ''
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    
    cli += ' switch %s port-show port %s hostname %s format trunk no-show-headers ' % (switch, switch_port, peer_switch)
    trunk = run_cli(module, cli).split()
    trunk = list(set(trunk))
    if len(trunk) > 0:
        cli = clicopy
        cli += ' switch %s trunk-delete name %s ' % (switch, trunk[0])
        output += run_cli(module, cli)
        output += ' '
    return output


def assign_loopback_ip(module,loopback_address):
    """
    This method is to add loopback interface to vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param loopback_address: The network ip of the ips to be assigned
    :return: The success or the error message.
    """
    output = ' '    
    address = loopback_address.split('.')
    static_part = str(address[0]) + '.' +  str(address[1]) + '.' + str(address[2]) + '.'
    dynamic = address[3]    
 
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()
    
    if len(vrouter_names) > 0:
        
        i = 1
        if len(vrouter_names) + i - 1 <= 255:
            for vrouter in vrouter_names:
                ip = static_part + str(i)
                
                cli = clicopy
                cli += ' vrouter-loopback-interface-show ip %s format switch no-show-headers ' % (ip)
                existing_vrouter = run_cli(module, cli).split()
                
                if vrouter not in existing_vrouter:
                    cli = clicopy
                    cli += ' vrouter-loopback-interface-add vrouter-name '
                    cli += vrouter
                    cli += ' ip %s ' % (ip)
                    output += run_cli(module, cli)
                    output += ' '
                i = i + 1   

        else:
            output += "Not enough ips for all the vrouters"
    else:
        output += "no vrouters present"

    return output   



def auto_configure_link_ips(module):
    """
    This method is to auto configure link IPs for layer3 fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of create_vrouter_and_interface() method.
    """
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    fabric_loopback = module.params['pn_assign_loopback']

    output = ' '    
    cli = pn_cli(module)
    clicopy = cli    


    cli = clicopy
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    switch_names = list(set(switch_names))
    
    for switch in switch_names:
        output += disable_trunk(module, switch)
        output += ' '

    address = module.params['pn_net_address']
    cidr = module.params['pn_cidr']
    supernet = module.params['pn_supernet']
    available_ips = calculate_link_ip_addresses(address, cidr, supernet)
  
    for switch in switch_names:
        output += create_vrouter(module, switch)
        output += ' '

    for spine in spine_list:
        for leaf in leaf_list:
            cli = clicopy
            cli += ' switch %s port-show hostname %s' % (leaf, spine)
            cli += ' format port no-show-headers '            
            leaf_port = run_cli(module, cli).split()
           
            while len(leaf_port) > 0:
                lport = leaf_port[0]
                ip = available_ips[0]                 
                output += delete_trunk(module, leaf, lport, spine)
                output += create_interface(module, leaf, ip, lport)
                output += ' '
                leaf_port.remove(lport)
                available_ips.remove(ip)
                ip = available_ips[0]
                #sport = spine_port[0]
                cli = clicopy
                cli += ' switch %s port-show port %s format rport no-show-headers ' % (leaf, lport)
                    
                sport = run_cli(module, cli)
                output += delete_trunk(module, spine, sport, leaf)
                output += create_interface(module, spine, ip, sport)
                available_ips.remove(ip)
                #spine_port.remove(sport)
                i = 0
                    
                diff = 32 - int(supernet)
                count = (1 << diff) - 4
                while i < count:
                    available_ips.pop(0)
                    i += 1         
             
          
    if fabric_loopback:
        loopback_address = module.params['pn_loopback_ip']
        output += assign_loopback_ip(module, loopback_address)
        output += ' '
    return output





def create_cluster(module, switch, name, node1, node2):
    """
    This method is to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    
    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % (node1)
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy 
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        return run_cli(module, cli)
    else:
        return "Already part of a cluster"



def get_ports(module, switch, peer_switch):
    """
    This method is to figure out connected ports between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param peer_switch: Name of the connected peer switch.
    :return: List of connected ports.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    cli += ' switch %s port-show hostname %s' % (switch, peer_switch)
    cli += ' format port no-show-headers '

    return run_cli(module, cli).split()



def create_trunk(module, switch, name, ports):
    """
    This method is to create a trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the trunk to create.
    :param ports: List of connected ports.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    cli += ' switch %s trunk-show format name no-show-headers ' % (switch)
    trunk_list = run_cli(module, cli).split()
    if name not in trunk_list:
        cli = clicopy
        ports_string = ','.join(ports)
        cli += ' switch %s trunk-create name %s ' % (switch, name)
        cli += ' ports %s ' % ports_string
        return run_cli(module, cli)
    else:
        return "Already part of a trunk"




def leaf_no_cluster(module, leaf_list):
    """
    This method is to find leafs which are not
    part of any cluster
    :param module: The Ansible module to fetch input parameters.
    :leaf_list: The list of leafs.
    :return: The leafs which are not part of any cluster.
    """
    cli = pn_cli(module)
    noncluster_leaf = []
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
   
    clicopy = cli
    clicopy += ' cluster-show format cluster-node-1 no-show-headers '
    cluster1 = run_cli(module, clicopy).split()
    clicopy = cli
    clicopy += ' cluster-show format cluster-node-2 no-show-headers '
    cluster2 = run_cli(module, clicopy).split()
    
    for leaf in leaf_list:
        if (leaf not in cluster1) and (leaf not in cluster2):
            noncluster_leaf.append(leaf)
        
    return noncluster_leaf



def create_vlag(module, switch, name, peer_switch, port, peer_port):
    """
    This method is to create virtual link aggregation groups.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the vlag to create.
    :param port: List of local switch ports.
    :param peer_switch: Name of the peer switch.
    :param peer_port: List of peer switch ports.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' switch %s vlag-show format name no-show-headers ' % (switch)
    vlag_list = run_cli(module, cli).split()
    if name not in vlag_list:
        cli = clicopy

        cli += ' switch %s vlag-create name %s port %s ' % (switch, name, port)
        cli += ' peer-switch %s peer-port %s mode active-active' % (peer_switch, peer_port)
        return run_cli(module, cli)
    else:
        return "Already part of a vlag"





def create_trunk_vlag(module, node1, dest_list):
    """
    The method is aggregation of create_trunk() and get_ports()
    to create a trunk
    :param module: The Ansible module to fetch input parameters.
    :param node1: The local node from which lag needs to be created.
    :param dest_list: The list of destination to know the 
     physical links port
    :return: It returns the name of the trunk created
    """
    output = ' '
    string2 = ''
    src_ports = []
    for node in dest_list:
        src_ports += get_ports(module, node1, node)
        string2 += str(node)

    src_ports = list(set(src_ports))
    
    name = node1[5:] + '-to-' + string2
    output += create_trunk(module, node1, name, src_ports)
    output += ' '
     
    return name






def create_leaf_cluster_vlag(module, noncluster_leaf, spine_list):
    """
    This method is to create clusters, lag and vlag for the switches having 
    physical links
    :param module: The Ansible module to fetch input parameters.
    :param noncluster_leaf: The list of leaf which are not part of any cluster
    :param spine_list: The list of spines
    :return: The output message related to vlag, lag and cluster creation
    """

    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli

    output = ' '

    flag = 0
    while flag == 0:
        if len(noncluster_leaf) == 0:
            output += "no more leaf to create cluster"
            output += ' '
            flag += 1
        else:
            node1 = noncluster_leaf[0]
            noncluster_leaf.remove(node1)
            cli = clicopy
            cli += ' switch %s lldp-show format sys-name no-show-headers ' % node1
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            flag1 = 0
            i = 0
            while (i < len(system_names)) and (flag1 == 0):
                node2 = system_names[i]
                if node2 not in spine_list:
                    if node2 in noncluster_leaf:
                        name = node1 + '-to-' + node2 + '-cluster'
                        output += create_cluster(module, node2, name, node1, switch)
                        output += ' '
                        noncluster_leaf.remove(node2)
                        name1 = create_trunk_vlag(module, node1, spine_list)
                        name2 = create_trunk_vlag(module, node2, spine_list)
                       
                        name = node1[5:] + node2 + '-to-' + 'spine'
                        output += create_vlag(module, node1, name, node2, name1, name2)           
                        output += ' '

                        list1 = []
                        list1.append(node1)
                        list1.append(node2)
                        spine1 = str(spine_list[0])
                        spine2 = str(spine_list[1])
                        name1 = create_trunk_vlag(module, spine1, list1)
                        name2 = create_trunk_vlag(module, spine2, list1)
                        name = spine1[5:] + spine2 + '-to' + node1 + node2 
                        output += create_vlag(module, spine1, name, spine2, name1, name2)
                        output += ' '

                        flag1 += 1
                    else:
                        print "switch already has a cluster"
                else:
                    print "switch is a spine"        
                
                i += 1
    return output





def create_vlan(module, start, end):
    """
    This method is to create vlans
    :param module: The Ansible module to fetch input parameters.
    
    :return: Success or failure message for the whole range.
    """
    vlan = []
    output = ' '
    cli = pn_cli(module)
    clicopy = cli
    clicopy += ' vlan-show format id no-show-headers '
    already_vlan_id = run_cli(module, clicopy).split()
    already_vlan_id = list(set(already_vlan_id))
    #already_vlan_id = ','.join(already_vlan_id)
    #already_vlan_id = already_vlan_id.split(',')
    #count = 0
    vlan_id = int(start)
    while vlan_id < int(end):
        id_str = str(vlan_id)
        vlan.append(id_str)
        if id_str not in already_vlan_id:
            #vlan.append(id_str)
            clicopy = cli
            clicopy += ' vlan-create id '
            clicopy += id_str
            clicopy += ' scope fabric '
            output += run_cli(module, clicopy)
            output += ' '
            #count += 1

        vlan_id += 1

    #if count == links:
    return vlan
    #else:
    #    return "vlans not created successfully"





def create_l2_vrouter(module, switch, vrrp_id):
    """
    This method is to create vrouter and vrouter interface and assign IP to it.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param available_ips: List of available IP addresses to be assigned to vrouter interfaces.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    """
    code changed
    removing first character from the vrouter name
    """
    output = ' '
    switch_temp = switch[3:]
    vrouter_name = switch_temp + '-vrouter'
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    cli += ' switch ' + switch
    cli_copy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = cli_copy
        cli += ' vrouter-create name %s vnet %s hw-vrrp-id %s enable ' % (vrouter_name, vnet_name, vrrp_id)
        run_cli(module, cli)
        output += ' Created vrouter %s on switch %s ' % (vrouter_name, switch)
    else:
        output += ' Vrouter name %s on switch %s already exists. ' % (vrouter_name, switch)

    return output




def create_l2_interface(module, switch, ip, vlan_id, vrrp_id, ip_count, vrrp_priority):

    output = ' '
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    cli += ' vrouter-show location %s format name no-show-headers ' % (switch)
    vrouter_name = run_cli(module, cli).split()
    ip_addr = ip.split('.')
    fourth = ip_addr[3].split('/')
    subnet = fourth[1]
    
    first = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.' 
    ip1 = first + '1' + '/' + subnet
    ip2 = first + ip_count + '/' + subnet

#    cli += ' switch ' + switch
#    cli_copy = cli

    # Check if vrouter already exists
#    cli += ' vrouter-interface-show format switch no-show-headers '
#    existing_vrouter_names = run_cli(module, cli).split()
    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s format switch no-show-headers ' % (vlan_id, ip2)
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))
    
    if vrouter_name[0] not in existing_vrouter:
    
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip2
        cli += ' vlan %s if data ' % (vlan_id)
        run_cli(module, cli)
        output += ' and added vrouter interface with ip: ' + ip2
        output += ' '
    else:
        output += ' interface already exists for vrouter %s ' % (vrouter_name[0])
    
    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s format nic no-show-headers ' % (vrouter_name[0], ip2, vlan_id )
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name[0])


      
    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s format switch no-show-headers ' % (vlan_id, ip1, eth_port[0])
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))






    if vrouter_name[0] not in existing_vrouter:
        
    
    
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip1
        cli += ' vlan %s if data vrrp-id %s vrrp-primary %s vrrp-priority %s ' % (vlan_id, vrrp_id, eth_port[0], vrrp_priority)
    
        output += run_cli(module, cli)
        output += ' '

    else:
        output += ' interface already added for vrouter %s ' % (vrouter_name[0])

    return output


def create_nonclusterleaf_vlag(module, noncluster_leaf, spine_list):
    """
    This method is to create lag and vlag for noncluster leafs
    :param module: The Ansible module to fetch input parameters.
    :param noncluster_leaf: The list of all noncluster leaf
    :param spine_list: The list of all spine_list
    :return: The output messages related to vlag creation
    """
    output = ' '
    for leaf in noncluster_leaf:
        create_trunk_vlag(module, leaf, spine_list)
        list1 = []
        list1.append(leaf)

        spine1 = str(spine_list[0])
        spine2 = str(spine_list[1])
        name1 = create_trunk_vlag(module, spine1, list1)
        name2 = create_trunk_vlag(module, spine2, list1)

        name = spine1[5:] + spine2 + '-to-' + leaf
        output += create_vlag(module, spine1, name, spine2, name1, name2)
        output += ' '
    return output




def configure_auto_vlag(module):
    """
    This method is to create and configure vlag.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    output = ' '
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']

    spine1 = spine_list[0]
    spine2 = spine_list[1]
    spine1_ports = []
    spine2_ports = []

    create_cluster(module, spine1, 'spine-cluster', spine1, spine2)

    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli

    noncluster_leaf = leaf_no_cluster(module, leaf_list)

    output += create_leaf_cluster_vlag(module, noncluster_leaf, spine_list)
    output = ' '
    noncluster_leaf = leaf_no_cluster(module, leaf_list)

    output += create_nonclusterleaf_vlag(module, noncluster_leaf, spine_list)
    output += ' '

    return output




#def configure_auto_vlag(module):
#    """
#    This method is to create and configure vlag.
#    :param module: The Ansible module to fetch input parameters.
#    :return: The output of run_cli() method.
#    """
#    output = ' '
#    #spine_list = module.params['pn_spine_list']
#    #leaf_list = module.params['pn_leaf_list']
#    spine_list = module.params['pn_spine_list']
#    leaf_list = module.params['pn_leaf_list']
#    
##    spine_list = ['auto-spine1', 'auto-spine2']
##    leaf_list = ['auto-leaf1','auto-leaf2','auto-leaf3','auto-leaf4']
#    spine1 = spine_list[0]
#    spine2 = spine_list[1]
#    spine1_ports = []
#    spine2_ports = []
#
#    create_cluster(module, spine1, 'spine-cluster', spine1, spine2)
#
#    for leaf in leaf_list:
#        spine1_ports += get_ports(module, spine1, leaf)
#        spine2_ports += get_ports(module, spine2, leaf)
#    spine1_ports = list(set(spine1_ports))
#    spine2_ports = list(set(spine2_ports))
#
#    create_trunk(module, spine1, 'spine1-to-leaf', spine1_ports)
#    create_trunk(module, spine2, 'spine2-to-leaf', spine2_ports)
#
#    create_vlag(module, spine1, 'spine-to-spine', spine2, 'spine1-to-leaf', 'spine2-to-leaf')
#
#    cli = pn_cli(module)
#    if 'switch' in cli:
#        cli = cli.rpartition('switch')[0]
#    clicopy = cli
# #   first_leaf = leaf_list[0]
# #   cli += ' switch %s lldp-show format sys-name no-show-headers ' % first_leaf
# #   sys_names = run_cli(module, cli).split()
#
#    noncluster_leaf = leaf_no_cluster(module, leaf_list)
#    
#    output += create_leaf_cluster_vlag(module, noncluster_leaf, spine_list)
#    output += ' '
#    #ip = '101.101.$.0/24'
#    #ip_segment = ip.split('.')
#    vrrp_id = module.params['pn_vrrp_id']
#    no_interface = module.params['pn_vrrp_no_interface']
#    vrrp_ip = module.params['pn_vrrp_ip']
#    active_switch = module.params['pn_active_switch']
#    vlan_range = module.params['pn_vlan_range']
#    #no_interface = '4'
#    #vlan_range = '101-200'
#    vlan_range_split = vlan_range.split('-')
#    start = vlan_range_split[0]
#    end = vlan_range_split[1]
#    end_no_interface = int(start) + int(no_interface)
#    vlan = create_vlan(module, start, end_no_interface)
#    #vlan = ['101','102','103','104']
#    #vrrp_id = '18'
#    output += ' vlans created '
#    for spine in spine_list:
#        output += create_l2_vrouter(module, spine, vrrp_id)
#        output += ' '
#    #vrrp_ip = '101.101.$.0/24'
#    #active_switch = 'auto-spine1'
#    vrrp_ip_segment = vrrp_ip.split('.')
#    #dict_count = { 'auto-spine1':'2' , 'auto-spine2':'3' }
#    host_count = 1 
#    for spine in spine_list:
#        host_count += 1
#        if spine == active_switch:
#            vrrp_priority = '110'
#        else:
#            vrrp_priority = '100'
#        for vlan_id in vlan:
#        
#            ip = vrrp_ip_segment[0] + '.' + vrrp_ip_segment[1] + '.' + vlan_id + '.' + vrrp_ip_segment[3]
#                        
#            output += create_l2_interface(module, spine, ip, vlan_id, vrrp_id, str(host_count), vrrp_priority)
#            if (int(vlan_id) % 15 == 0):
#                output += ' waiting for 2 sec '            
#                time.sleep(2)
#
#    return output




def assign_inband_ip(module, inband_address):
    """
    This method is to assign inband ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :inband_address: The network ip for the inband ips.
    :return: The output messages for assignment.
    """
    output = ''
    #inband_address = module.params['pn_inband_ip']
    
    address = inband_address.split('.')
    static_part = str(address[0]) + '.' +  str(address[1]) + '.' + str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]
    dynamic = int(last_octet[0])
 
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()

    if len(switch_names) > 0:

        i = 1
        if len(switch_names) + i - 1 <= 255:
            for switch in switch_names:
                ip = static_part + str(i) + '/' + subnet

                cli = clicopy
                cli += ' switch %s switch-setup-modify ' % (switch)
              
                cli += ' in-band-ip %s ' % (ip)
                output += run_cli(module, cli)
                output += ' '
                i = i + 1

        else:
            output += "Not enough inband-ips for all the switches"
    else:
        output += "No switches present"

    return output






def main():
    """ This section is for arguments parsing """

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            pn_fabric_name=dict(required=False, type='str'),
            pn_fabric_network=dict(required=False, type='str',
                                   choices=['mgmt', 'in-band'],
                                   default='mgmt'),
            pn_fabric_type=dict(required=False, type='str',
                                choices=['layer2', 'layer3'],
                                default='layer2'),
            pn_fabric_retry=dict(required=False, type='int', default=1),
            pn_run_l2_l3=dict(required=False, type='bool', default=False),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabricto_inband=dict(required=False, type='bool', default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str', default='101.101.101.0/32'),
            pn_inband_ip=dict(required=False, type='str', default='172.16.0.0/24'),
            pn_fabric_control_network=dict(required=False, type='str', choices=['mgmt', 'in-band'], default='mgmt'),
            pn_protocol=dict(required=False, type='str'),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_vrrp_ip=dict(required=False, type='str', dafault='101.101.$.0/24'),
            pn_active_switch=dict(required=False, type='str', default='auto-spine1'),
            pn_vlan_range=dict(required=False, type='str', default='101-200'),
            pn_vrrp_no_interface=dict(required=False, type='str', default='4')
  

        )
    )

    fabric_name = module.params['pn_fabric_name']
    fabric_network = module.params['pn_fabric_network']
    fabric_type = module.params['pn_fabric_type']
    run_l2_l3 = module.params['pn_run_l2_l3']
    control_network = module.params['pn_fabric_control_network']
    update_fabricto_inband = module.params['pn_update_fabricto_inband']

    inband_address = module.params['pn_inband_ip']    
    message = ' '
    
 

    if not run_l2_l3:

        #pass   
        #message += "------------------------------------------------------------------------#####################################"
        message += auto_accept_eula(module)
        #message += ' '
        #message += switch_setup(module)

        message += ' eula accepted '
        message += create_fabric(module, fabric_name, fabric_network)
        message += ' '
        message += configure_control_network(module, control_network)
        message += ' control network to management '
        message += modify_stp(module, 'disable')
        message += ' stp disable '
        message += enable_ports(module)
        message += ' ports enable '

    else:
        
        message += assign_inband_ip(module, inband_address)

        if fabric_type == 'layer2':
            message += configure_auto_vlag(module)
           
        elif fabric_type == 'layer3':
            message += auto_configure_link_ips(module)

        if update_fabricto_inband:         
            message += ' '
            message += update_fabric_network_to_inband(module)
        message += ' '
        message += modify_stp(module, 'enable')
        message += ' '
  


    module.exit_json(
        stdout=message,        
        error="0",
        failed=False,
        msg="Operation Completed",
        changed=True
        )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

