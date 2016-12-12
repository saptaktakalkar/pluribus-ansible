import shlex
import json
import time


DOCUMENTATION = """
---
module: pn_ztp
author: "Pluribus Networks (@gauravbajaj)"
version: 1
short_description: CLI command to do zero touch provisioning with vrrp.
description: 
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Configure VRRP for the gateway(extension of l2 
          in the ZTP module)

options: TO DO

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










def create_vlan(module, start, end):
    """
    This method is to create vlans
    :param module: The Ansible module to fetch input parameters.
    :param start: Start of the vlan range for vlans to be created.
    :param end: End of the vlan range for vlans to be created.
    :return: Success or failure message for the vlans.
    """
    vlan = []
    output = ' '
    cli = pn_cli(module)
    clicopy = cli
    clicopy += ' vlan-show format id no-show-headers '
    already_vlan_id = run_cli(module, clicopy).split()
    already_vlan_id = list(set(already_vlan_id))
    
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

        vlan_id += 1

    #if count == links:
    return vlan
    #else:
    #    return "vlans not created successfully"





def create_l2_vrouter(module, switch, vrrp_id):
    """
    This method is to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vrrp_id: The vrrp_id to be assigned.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    
    #code changed
    #removing first character from the vrouter name
    
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
    """
    This method is to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned
    :vrrp_priority: priority to be given(110 for active switch).
    :ip_count: The value of fourth octet in the ip
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """

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







def configure_vrrp(module, vrrp_id, no_interface, vrrp_ip, active_switch, vlan_range):
    """
    This method is to configure vrrp.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id need to be assigned.
    :param no_interfaces: The number of interfaces to be added.
    :param vrrp_ip: The vrrp_ip needed to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_range: The vlan_range for creating the vlans.
    :return: It returns the output of the configuration
    """
    output = ' '
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']

    #vrrp_id = module.params['pn_vrrp_id']
    #no_interface = module.params['pn_vrrp_no_interface']
    #vrrp_ip = module.params['pn_vrrp_ip']
    #active_switch = module.params['pn_active_switch']
    #vlan_range = module.params['pn_vlan_range']
    #no_interface = '4'
    #vlan_range = '101-200'
    vlan_range_split = vlan_range.split('-')
    start = vlan_range_split[0]
    end = vlan_range_split[1]
    end_no_interface = int(start) + int(no_interface)
    vlan = create_vlan(module, start, end_no_interface)
    #vlan = ['101','102','103','104']
    #vrrp_id = '18'
    output += ' vlans created '
    for spine in spine_list:
        output += create_l2_vrouter(module, spine, vrrp_id)
        output += ' '
    #vrrp_ip = '101.101.$.0/24'
    #active_switch = 'auto-spine1'
    vrrp_ip_segment = vrrp_ip.split('.')
    host_count = 1
    for spine in spine_list:
        host_count += 1
        if spine == active_switch:
            vrrp_priority = '110'
        else:
            vrrp_priority = '100'

        for vlan_id in vlan:
            ip = vrrp_ip_segment[0] + '.' + vrrp_ip_segment[1] + '.' + vlan_id + '.' + vrrp_ip_segment[3]
            output += create_l2_interface(module, spine, ip, vlan_id, vrrp_id, str(host_count), vrrp_priority)
            if (int(vlan_id) % 15 == 0):
                output += ' waiting for 2 sec '
                time.sleep(2)

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


    vrrp_id = module.params['pn_vrrp_id']
    no_interface = module.params['pn_vrrp_no_interface']
    vrrp_ip = module.params['pn_vrrp_ip']
    active_switch = module.params['pn_active_switch']
    vlan_range = module.params['pn_vlan_range']


    message += ' '
    message += configure_vrrp(module)
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










