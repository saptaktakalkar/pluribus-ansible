# pn_initial_ztp

 Zero Touch Provisioning (ZTP) allows you to provision new switches in your network automatically, without manual intervention.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to provision new switches in the network automatically, without manual intervention. It performs the following tasks:
  
- Accept EULA
- Disable STP 
- Enable all ports
- Create/Join fabric
- Enable STP
      
## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_fabric\_name   | yes            |               | str         |               | Specify name of the fabric.                                |
| pn_fabric\_network| no             | mgmt          | str         | mgmt, in-band | Specify fabric network as either mgmt or in-band.          |
| pn_fabric\_control\_network| no     | mgmt          | str         | mgmt, in-band | Specify fabric control network as either mgmt or in-band.  |
| pn_toggle\_40g    | no             | True          | bool        |               | Flag to indicate if 40g ports should be converted to 10g ports.|
| pn_inband\_ip     | no             | 172.16.0.0/24 | str         |               | Inband IPs to be assigned to switches starting with this value.|
| pn_current\_switch| yes            |               | str         |               | Name of the switch on which this task is currently getting executed.|
| pn_static\_setup  | no             | False         | bool        |               | Flag to indicate if static values should be assigned to the switch setup parameters(\*).|
| pn_mgmt\_ip       | no(\*)         |         | str         |               | Specify mgmt IP value to be assigned if pn_static\_setup is True.|
| pn_mgmt\_ip\_subnet| no(\*)        |         | str         |               | Specify subnet mask of mgmt IP to be assigned if pn_static\_setup is True.|
| pn_gateway\_ip  | no(\*) |  | str |   |Specify the gateway IP to be assigned if `pn_static_setup` is True. |
| pn_dns\_ip | no(\*) |  | str | | Specify the DNS IP to be assigned if `pn_static_setup` is True. |
| pn_dns\_secondary\_ip | no(\*) |  | str | | Specify the Secondary DNS IP to be assigned if pn_static\_setup is True. |
| pn_domain\_name | no(\*) |  | str | | Specify the domain name to be assigned if pn_static\_setup is True. |
| pn_ntp\_server | no(\*) | | str | | Specify the NTP server to be assigned if pn_static\_setup is True. |
| pn_web\_api | no | True | bool | | Flag to enable web api. |
| pn_stp | no | False | bool | | Flag to enable STP at the end. |



## Examples

```
---


# This task is to configure initial ZTP setup on all switches.
# It uses pn_initial_ztp.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml.
# pn_current_switch and pn_mgmt_ip comes from the hosts file.
- name: Zero Touch Provisioning - Initial setup
  hosts: all
  serial: 1
  become: true
  become_method: su
  become_user: root

  vars_files:
  - cli_vault.yml

  tasks:
    - name: Auto accept EULA, Disable STP, enable ports and create/join fabric
      pn_initial_ztp:
        pn_cliusername: "{{ USERNAME }}"               # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"               # Cli password (value comes from cli_vault.yml).
        pn_fabric_name: 'ztp-fabric'                   # Name of the fabric to create/join.
        pn_current_switch: "{{ inventory_hostname }}"  # Name of the switch on which this task is currently getting executed.
        # pn_toggle_40g: True                          # Flag to indicate if 40g ports should be converted to 10g ports or not.
        # pn_inband_ip: '172.16.1.0/24'                # Inband ips to be assigned to switches starting with this value. Default: 172.16.0.0/24.
        # pn_fabric_network: 'mgmt'                    # Choices: in-band or mgmt.  Default: mgmt
        # pn_fabric_control_network: 'mgmt'            # Choices: in-band or mgmt.  Default: mgmt
        # pn_static_setup: False                       # Flag to indicate if static values should be assign to following switch setup params. Default: True.
        # pn_mgmt_ip: "{{ ansible_host }}"             # Specify MGMT-IP value to be assign if pn_static_setup is True.
        # pn_mgmt_ip_subnet: '16'                      # Specify subnet mask for MGMT-IP value to be assign if pn_static_setup is True.
        # pn_gateway_ip: '10.9.9.0'                    # Specify GATEWAY-IP value to be assign if pn_static_setup is True.
        # pn_dns_ip: '10.20.41.1'                      # Specify DNS-IP value to be assign if pn_static_setup is True.
        # pn_dns_secondary_ip: '10.20.4.1'             # Specify DNS-SECONDARY-IP value to be assign if pn_static_setup is True.
        # pn_domain_name: 'pluribusnetworks.com'       # Specify DOMAIN-NAME value to be assign if pn_static_setup is True.
        # pn_ntp_server: '0.us.pool.ntp.org'           # Specify NTP-SERVER value to be assign if pn_static_setup is True.
        # pn_web_api: True                             # Flag to enable web api. Default: True
        # pn_stp: False                                # Specify True if you want to enable STP at the end. Default: False.

      register: ztp_out                                # Variable to hold/register output of the above tasks.

    - debug:
        var: ztp_out.stdout_lines                      # Print stdout_lines of register variable.
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
