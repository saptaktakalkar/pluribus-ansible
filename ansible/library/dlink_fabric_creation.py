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

import shlex
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
    pn_switch_list:
      description:
        - Specify list of switches.
      required: False
      type: list
    pn_fabric_name:
      description:
        - Specify name of the fabric.
      required: False
      type: str
    pn_inband_ip:
      description:
        - Inband ips to be assigned to switches starting with this value.
      required: False
      default: 172.16.0.0/24.
      type: str
    pn_switch:
      description:
        - Name of the switch on which this task is currently getting executed.
      required: False
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
      pn_switch: "{{ inventory_hostname }}"
      pn_switch_list: "{{ groups['switch'] }}"
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
            'switch': module.params['pn_switch'],
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

    switches_list = module.params['pn_switch_list']
    switch = module.params['pn_switch']

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
            cli += ' in-band-ip %s ' % ip
            run_cli(module, cli)
            CHANGED_FLAG.append(True)
            output += 'Assigned in-band ip %s' % ip

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
    local_ports = run_cli(module, cli)

    if local_ports is not None:
        local_ports = local_ports.split()
    else:
        local_ports = []

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
        cli += ' switch-local stp-modify %s ' % modify_flag
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
        cli += ' fabric-local-modify control-network %s ' % network
        run_cli(module, cli)


def make_switch_setup_static(module):
    """
    Method to assign static values to different switch setup parameters.
    :param module: The Ansible module to fetch input parameters.
    """
    dns_ip = module.params['pn_dns_ip']
    dns_secondary_ip = module.params['pn_dns_secondary_ip']
    domain_name = module.params['pn_domain_name']
    ntp_server = module.params['pn_ntp_server']

    cli = pn_cli(module)
    cli += ' switch-setup-modify '

    if dns_ip:
        cli += ' dns-ip ' + dns_ip

    if dns_secondary_ip:
        cli += ' dns-secondary-ip ' + dns_secondary_ip

    if domain_name:
        cli += ' domain-name ' + domain_name

    if ntp_server:
        cli += ' ntp-server ' + ntp_server

    clicopy = cli
    if clicopy.split('switch-setup-modify')[1] != ' ':
        run_cli(module, cli)


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


def is_switches_connected(module):
    """
    Check if switches are physically connected to each other.
    :param module: The Ansible module to fetch input parameters.
    :return: True if connected else False.
    """
    cli = pn_cli(module)
    cli += ' lldp-show format switch,sys-name parsable-delim , '
    sys_names = run_cli(module, cli)

    if sys_names is not None:
        switch1 = module.params['pn_switch_list'][0]
        switch2 = module.params['pn_switch_list'][1]

        sys_names = list(set(sys_names.split()))
        for cluster in sys_names:
            if switch1 in cluster and switch2 in cluster:
                return True

    return False


def configure_fabric(module):
    """
    Create/join fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if fabric got created/joined/already configured.
    """
    switch_list = module.params['pn_switch_list']
    switch = module.params['pn_switch']
    fabric_name = module.params['pn_fabric_name']

    cli = pn_cli(module)
    cli += ' fabric-info format name no-show-headers '
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    # Above fabric-info cli command will throw an error, if switch is not part
    # of any fabric. So if err, we need to create/join the fabric.
    if err:
        if len(switch_list) == 2:
            if not is_switches_connected(module):
                msg = 'Error: Switches are not connected to each other'
                results = {
                    'switch': switch,
                    'output': msg
                }
                module.exit_json(
                    unreachable=False,
                    failed=True,
                    exception=msg,
                    summary=results,
                    task='Fabric creation',
                    msg='Fabric creation failed',
                    changed=False
                )

            new_fabric = False
            cli = pn_cli(module)
            cli += ' fabric-show format name no-show-headers '
            existing_fabrics = run_cli(module, cli)

            if existing_fabrics is not None:
                existing_fabrics = existing_fabrics.split()
                if fabric_name not in existing_fabrics:
                    new_fabric = True

            if new_fabric or existing_fabrics is None:
                output = create_fabric(module, fabric_name)
            else:
                output = join_fabric(module, fabric_name)
        else:
            output = create_fabric(module, fabric_name)
    else:
        return 'Fabric already configured'

    return output


def update_switch_names(module, switch_name):
    """
    Method to update switch names.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name to assign to the switch.
    :return: String describing switch name got modified or not.
    """
    cli = pn_cli(module)
    cli += ' switch-setup-show format switch-name '
    if switch_name == run_cli(module, cli).split()[1]:
        return ' Switch name is same as hostname! '
    else:
        cli = pn_cli(module)
        cli += ' switch-setup-modify switch-name ' + switch_name
        run_cli(module, cli)
        return ' Updated switch name to match hostname! '


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(argument_spec=dict(
        pn_cliusername=dict(required=False, type='str'),
        pn_clipassword=dict(required=False, type='str', no_log=True),
        pn_switch_list=dict(required=False, type='list', default=[]),
        pn_fabric_name=dict(required=True, type='str'),
        pn_inband_ip=dict(required=False, type='str', default='172.16.0.0/24'),
        pn_switch=dict(required=False, type='str'),
        pn_toggle_40g=dict(required=False, type='bool', default=True),
        pn_dns_ip=dict(required=False, type='str', default=''),
        pn_dns_secondary_ip=dict(required=False, type='str', default=''),
        pn_domain_name=dict(required=False, type='str', default=''),
        pn_ntp_server=dict(required=False, type='str', default=''), )
                          )

    global CHANGED_FLAG
    results = []
    switch = module.params['pn_switch']

    # Update switch names to match host names from hosts file
    update_switch_names(module, switch)

    # Create/join fabric
    out = configure_fabric(module)
    results.append({
        'switch': switch,
        'output': out
    })

    # Determine 'msg' field of JSON that will be returned at the end
    msg = out if 'already configured' in out else 'Fabric creation succeeded'

    # Configure fabric control network to mgmt
    configure_control_network(module)

    # Update switch setup values
    make_switch_setup_static(module)

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
                'switch': switch,
                'output': 'Toggled 40G ports to 10G'
            })

    # Assign in-band ips.
    out = assign_inband_ip(module)
    if out:
        results.append({
            'switch': switch,
            'output': out
        })

    # Enable STP
    modify_stp(module, 'enable')

    # Exit the module and return the required JSON
    module.exit_json(
        unreachable=False,
        msg=msg,
        summary=results,
        exception='',
        task='Fabric creation',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )

if __name__ == '__main__':
    main()
