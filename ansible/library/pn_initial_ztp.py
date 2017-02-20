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

from ansible.module_utils.basic import AnsibleModule
import shlex

DOCUMENTATION = """
---
module: pn_initial_ztp
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: CLI command to do zero touch provisioning.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Accept EULA
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
    pn_fabric_control_network:
      description:
        - Specify fabric control network as either mgmt or in-band.
      required: False
      type: str
      choices: ['mgmt', 'in-band']
      default: 'mgmt'
    pn_toggle_40g:
      description:
        - Flag to indicate if 40g ports should be converted to 10g ports or not.
      required: False
      default: True
      type: bool
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
    pn_static_setup:
      description:
        - Flag to indicate if static values should be assign to
        following switch setup params.
      required: False
      default: False
      type: bool
    pn_mgmt_ip:
      description:
        - Specify MGMT-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_mgmt_ip_subnet:
      description:
        - Specify subnet mask for MGMT-IP value to be assign if
        pn_static_setup is True.
      required: False
      type: str
    pn_gateway_ip:
      description:
        - Specify GATEWAY-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_dns_ip:
      description:
        - Specify DNS-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_dns_secondary_ip:
      description:
        - Specify DNS-SECONDARY-IP value to be assign if pn_static_setup is True
      required: False
      type: str
    pn_domain_name:
      description:
        - Specify DOMAIN-NAME value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_ntp_server:
      description:
        - Specify NTP-SERVER value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_web_api:
      description:
        - Flag to enable web api.
      default: True
      type: bool
    pn_stp:
      description:
        - Flag to enable STP at the end.
      required: False
      default: False
      type: bool
"""

EXAMPLES = """
- name: Auto accept EULA, Disable STP, enable ports and create/join fabric
    pn_initial_ztp:
      pn_cliusername: "{{ USERNAME }}"
      pn_clipassword: "{{ PASSWORD }}"
      pn_fabric_name: 'ztp-fabric'
      pn_current_switch: "{{ inventory_hostname }}"
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


def make_switch_setup_static(module):
    """
    Method to assign static values to different switch setup parameters.
    :param module: The Ansible module to fetch input parameters.
    """
    mgmt_ip = module.params['pn_mgmt_ip']
    mgmt_ip_subnet = module.params['pn_mgmt_ip_subnet']
    gateway_ip = module.params['pn_gateway_ip']
    dns_ip = module.params['pn_dns_ip']
    dns_secondary_ip = module.params['pn_dns_secondary_ip']
    domain_name = module.params['pn_domain_name']
    ntp_server = module.params['pn_ntp_server']

    if mgmt_ip:
        cli = pn_cli(module)
        ip = mgmt_ip + '/' + mgmt_ip_subnet
        cli += ' switch-setup-modify mgmt-ip ' + ip
        run_cli(module, cli)

    if gateway_ip:
        cli = pn_cli(module)
        cli += ' switch-setup-modify gateway-ip ' + gateway_ip
        run_cli(module, cli)

    if dns_ip:
        cli = pn_cli(module)
        cli += ' switch-setup-modify dns-ip ' + dns_ip
        run_cli(module, cli)

    if dns_secondary_ip:
        cli = pn_cli(module)
        cli += ' switch-setup-modify dns-secondary-ip ' + dns_secondary_ip
        run_cli(module, cli)

    if domain_name:
        cli = pn_cli(module)
        cli += ' switch-setup-modify domain-name ' + domain_name
        run_cli(module, cli)

    if ntp_server:
        cli = pn_cli(module)
        cli += ' switch-setup-modify ntp-server ' + ntp_server
        run_cli(module, cli)


def modify_stp_local(module, modify_flag):
    """
    Method to enable/disable STP (Spanning Tree Protocol) on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param modify_flag: Enable/disable flag to set.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' switch-local stp-show format enable '
    current_state = run_cli(module, cli).split()[1]

    if current_state == 'yes':
        cli = pn_cli(module)
        cli += ' switch-local stp-modify ' + modify_flag
        return run_cli(module, cli)
    else:
        return ' STP is already disabled! '


def configure_control_network(module, network):
    """
    Method to configure the fabric control network.
    :param module: The Ansible module to fetch input parameters.
    :param network: It can be in-band or management.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' fabric-info format control-network '
    current_control_network = run_cli(module, cli).split()[1]

    if current_control_network == network:
        return ' Fabric is already in %s control network ' % network
    else:
        cli = pn_cli(module)
        cli += ' fabric-local-modify control-network ' + network
        return run_cli(module, cli)


def enable_ports(module):
    """
    Method to enable all ports of a switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' port-config-show format port no-show-headers '
    out = run_cli(module, cli)

    cli = pn_cli(module)
    cli += ' port-config-show format port speed 40g no-show-headers '
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
            cli = pn_cli(module)
            cli += ' port-config-modify port %s enable ' % ports
            return run_cli(module, cli)
    else:
        return out


def create_or_join_fabric(module, fabric_name, fabric_network):
    """
    Method to create/join a fabric with default fabric type as mgmt.
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to create/join.
    :param fabric_network: Type of the fabric to create (mgmt/in-band).
    Default value: mgmt
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    clicopy = cli

    cli += ' fabric-show format name no-show-headers '
    fabrics_names = run_cli(module, cli).split()

    if fabric_name not in fabrics_names:
        cli = clicopy
        cli += ' fabric-create name ' + fabric_name
        cli += ' fabric-network ' + fabric_network
    else:
        cli = clicopy
        cli += ' fabric-info format name no-show-headers'
        cli = shlex.split(cli)
        rc, out, err = module.run_command(cli)

        if err:
            cli = clicopy
            cli += ' fabric-join name ' + fabric_name
        elif out:
            present_fabric_name = out.split()
            if present_fabric_name[1] not in fabrics_names:
                cli = clicopy
                cli += ' fabric-join name ' + fabric_name
            else:
                return 'Switch already in the fabric'

    return run_cli(module, cli)


def enable_web_api(module):
    """
    Method to enable web api on switches.
    :param module: The Ansible module to fetch input parameters.
    """
    cli = pn_cli(module)
    cli += ' admin-service-modify web if mgmt '
    run_cli(module, cli)


def toggle_40g_local(module):
    """
    Method to toggle 40g ports to 10g ports.
    :param module: The Ansible module to fetch input parameters.
    :return: The output messages for assignment.
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
    if len(ports_40g) > 0 and ports_40g != 'Success':
        ports_40g = ports_40g.split()
        ports_to_modify = list(set(ports_40g) - set(local_ports))

        for port in ports_to_modify:
            end_port = int(port) + 4
            range_port = port + '-' + str(end_port)

            cli = clicopy
            cli += ' switch-local port-config-modify port %s ' % range_port
            cli += ' speed disable '
            output += 'port range_port ' + range_port + ' disabled'
            output += run_cli(module, cli)

            cli = clicopy
            cli += ' switch-local port-config-modify port %s ' % range_port
            cli += ' speed 10g '
            output += 'port range_port ' + range_port + ' 10g converted'
            output += run_cli(module, cli)

            cli = clicopy
            cli += ' switch-local port-config-modify port %s ' % range_port
            cli += ' enable '
            output += 'port range_port ' + range_port + '  enabled'
            output += run_cli(module, cli)

    return output


def assign_inband_ip(module, inband_address):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :param inband_address: The network ip for the in-band ips.
    :return: String describing if in-band ip got assigned or not.
    """
    global CHANGED_FLAG
    output = ''
    address = inband_address.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    # Get the list of all switches present in fabric.
    cli = pn_cli(module)
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    switch_names.sort()

    if len(switch_names) > 0:
        ip_count = 0
        for switch in switch_names:
            if ip_count <= 255:
                ip_count += 1
                ip = static_part + str(ip_count) + '/' + subnet
                # Get existing in-band ip.
                cli = clicopy
                cli += ' fabric-node-show name %s format in-band-ip ' % switch
                cli += ' no-show-headers '
                existing_inband_ip = run_cli(module, cli).split()[0]
                # If existing in-band ip is not the same then assign new ip.
                if ip != existing_inband_ip:
                    cli = clicopy
                    cli += ' fabric-node-show format in-band-ip '
                    cli += ' no-show-headers '
                    assigned_ips = run_cli(module, cli).split()
                    # Make sure ip has not been assigned to any of the switches.
                    while ip in assigned_ips:
                        # If ip is not unique, increase the ip count by 1.
                        ip_count += 1
                        ip = static_part + str(ip_count) + '/' + subnet

                    # Assign unique in-band ip to the switch.
                    cli = clicopy
                    cli += ' switch %s switch-setup-modify ' % switch
                    cli += ' in-band-ip ' + ip
                    if 'Setup completed successfully' in run_cli(module, cli):
                        output += ' Assigned in-band ip %s to %s! ' % (ip,
                                                                       switch)
                        CHANGED_FLAG.append(True)

                else:
                    output += ' %s has been already assigned to %s! ' % (ip,
                                                                         switch)
                    CHANGED_FLAG.append(False)
            else:
                output += ' Not enough in-band ips available for all switches! '
                CHANGED_FLAG.append(False)
    else:
        output += ' No switches present in fabric for in-band ips assignment! '
        CHANGED_FLAG.append(False)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
            pn_fabric_network=dict(required=False, type='str',
                                   choices=['mgmt', 'in-band'],
                                   default='mgmt'),
            pn_fabric_control_network=dict(required=False, type='str',
                                           choices=['mgmt', 'in-band'],
                                           default='mgmt'),
            pn_toggle_40g=dict(required=False, type='bool', default=True),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_current_switch=dict(required=False, type='str'),
            pn_static_setup=dict(required=False, type='bool', default=False),
            pn_mgmt_ip=dict(required=False, type='str'),
            pn_mgmt_ip_subnet=dict(required=False, type='str'),
            pn_gateway_ip=dict(required=False, type='str'),
            pn_dns_ip=dict(required=False, type='str'),
            pn_dns_secondary_ip=dict(required=False, type='str'),
            pn_domain_name=dict(required=False, type='str'),
            pn_ntp_server=dict(required=False, type='str'),
            pn_web_api=dict(type='bool', default=True),
            pn_stp=dict(required=False, type='bool', default=False),
        )
    )

    fabric_name = module.params['pn_fabric_name']
    fabric_network = module.params['pn_fabric_network']
    control_network = module.params['pn_fabric_control_network']
    toggle_40g_flag = module.params['pn_toggle_40g']
    current_switch = module.params['pn_current_switch']
    message = ''
    global CHANGED_FLAG
    CHANGED_FLAG = []

    # Auto accept EULA
    eula_out_msg = auto_accept_eula(module)
    if 'Setup completed successfully' in eula_out_msg:
        message += ' EULA accepted on %s! ' % current_switch
        CHANGED_FLAG.append(True)
    else:
        message += eula_out_msg
        CHANGED_FLAG.append(False)

    # Update switch names to match host names from hosts file
    if 'Updated' in update_switch_names(module, current_switch):
        CHANGED_FLAG.append(True)
    else:
        CHANGED_FLAG.append(False)

    # Make switch setup static
    if module.params['pn_static_setup']:
        make_switch_setup_static(module)

    # Create/join fabric
    if 'already in the fabric' in create_or_join_fabric(module, fabric_name,
                                                        fabric_network):
        message += ' %s is already in fabric %s! ' % (current_switch,
                                                      fabric_name)
        CHANGED_FLAG.append(False)
    else:
        message += ' %s has joined fabric %s! ' % (current_switch,
                                                   fabric_name)
        CHANGED_FLAG.append(True)

    # Configure fabric control network to either mgmt or in-band
    net_out_msg = configure_control_network(module, control_network)
    if 'Success' in net_out_msg:
        message += ' Configured fabric control network to %s on %s! ' % (
            control_network, current_switch)
        CHANGED_FLAG.append(True)
    else:
        message += net_out_msg
        CHANGED_FLAG.append(False)

    # Enable web api if flag is True
    if module.params['pn_web_api']:
        enable_web_api(module)

    # Disable STP
    stp_out_msg = modify_stp_local(module, 'disable')
    if 'Success' in stp_out_msg:
        message += ' STP disabled on %s! ' % current_switch
        CHANGED_FLAG.append(True)
    else:
        message += stp_out_msg
        CHANGED_FLAG.append(False)

    # Enable ports
    ports_out_msg = enable_ports(module)
    if 'Success' in ports_out_msg:
        message += ' Ports enabled on %s! ' % current_switch
        CHANGED_FLAG.append(True)
    else:
        message += ports_out_msg
        CHANGED_FLAG.append(False)

    # Toggle 40g ports to 10g
    if toggle_40g_flag:
        if toggle_40g_local(module):
            message += ' Toggled 40G ports to 10G on %s! ' % current_switch
            CHANGED_FLAG.append(True)
        else:
            CHANGED_FLAG.append(False)

    # Assign in-band ips.
    message += assign_inband_ip(module, module.params['pn_inband_ip'])

    # Enable STP if flag is True
    if module.params['pn_stp']:
        stp_out_msg = modify_stp_local(module, 'enable')
        if 'Success' in stp_out_msg:
            message += ' STP enabled on %s! ' % current_switch
            CHANGED_FLAG.append(True)
        else:
            message += stp_out_msg
            CHANGED_FLAG.append(False)

    # Exit the module and return the required JSON
    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

