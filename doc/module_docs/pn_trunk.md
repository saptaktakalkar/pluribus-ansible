# pn_trunk

 Module for CLI trunk configurations. Supports `trunk-create`, `trunk-delete` and `trunk-modify` commands with options.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  Trunks can be used to aggregate network links at Layer 2 on the local switch.
  
## Options

| parameter       | required       | default      |choices       |comments                                                    |
|-----------------|----------------|--------------|--------------|------------------------------------------------------------|
| pn_cliusername  | yes            |              |              | Login username.                                            |
| pn_clipassword  | yes            |              |              | Login password.                                            |
| pn_cliswitch    | no             |              |              | Target switch(es) to run command on.                       |
| pn_command      | yes            |              | trunk-create, trunk-delete, trunk-modify | Create, delete, modify trunk configurations.|
| pn_name         | yes            |              |              | Specify the name for the trunk configuration.                           |
| pn_ports        | for trunk-create |            |              | Specify the the port number(s) for the link(s) to aggregate into trunk. |
| pn_speed        | no             |              | disable, 10m, 100m, 1g, 2.5g, 10g, 40g | Specify the port speed or disable the port speed.| 
| pn_egress_rate_limit| no         |              |              | Specify an egress port data rate limit for the configuration.|
| pn_jumbo        | no             |              | True, False  | Specify if the port can receive jumbo frames.              |
| pn_lacp_mode    | no             |              | off, passive, active | Specify the LACP mode for the configuration.       |
| pn_lacp_priority| no             |              |              | Specify the LACP priority. This is a number between 1 and 65535 with a default value of 32768.|
| pn_lacp_timeout | no             |              | slow, fast   | Specify the LACP timeout as slow(30s) or fast(4s). Default value is slow.|
| pn_lacp_fallback| no             |              | bundle, individual| Specify the LACP fallback mode.                       |
| pn_lacp_fallback_timeout| no     |              |              | Specify the LACP fallback timeout in seconds. The range is between 30 and 60 seconds with a default value of 50 seconds. |
| pn_edge_switch  | no             |              | True, False  | Specify if the switch is an edge switch.                   |
| pn_pause        | no             |              | True, False  | Specify if pause frames are sent.                          |
| pn_description  | no             |              |              | Specify a description for the trunk configuration.         |
| pn_loopback     | no             |              | True, False  | Specify loopback if you want to use loopback.              |
| pn_mirror_receive| no            |              | True, False  | Specify if the configuration receives mirrored traffic.    |
| pn_unknown_ucast_level | no      |              |              | Specify an unknown unicast level in percent. Default is 100%. |
| pn_unknown_mcast_level | no      |              |              | Specify an unknown multicast level in percent. Default is 100%. |
| pn_broadcast_level| no           |              |              | Specify a known broadcast level.                           |
| pn_port_macaddr | no             |              |              | Specify the mac address of the port.                       |
| pn_loopvlans    | no             |              |              | Specify a list of looping VLANs.                           |
| pn_routing      | no             |              | True, False  | Specify if the port participates in routing on the network.|
| pn_host         | no             |              | True, False  | Host config port control setting.                          |
| pn_quiet        | no             | true         |              | Enable/disable system information.                         |


## Usage

```
- name: "Playbook for CLI trunk"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN trunk command"
    pn_vlan: >
      pn_cliusername=<username> 
      pn_clipassword=<password> 
      pn_command=<trunk-create/delete/modify> 
      pn_name=<name> 
      [pn_ports=<ports>]
      [pn_quiet=<True/False>]
  
```

## Examples

# trunk-create
Sample playbook for **_creating_** a trunk configuration.
```
---
- name: "Playbook for trunk Create"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Create trunk"
    pn_trunk: pn_cliusername=<username> pn_clipassword=<password> pn_command='trunk-create' pn_name='ansible-trunk' pn_ports='11,12,13,14'
    register: cmd_output
  - debug: var=cmd_output
  
```

# trunk-delete
Sample playbook for **_deleting_** a trunk configuration.
```
---
- name: "Playbook for trunk Delete"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Delete trunk"
    pn_trunk: pn_cliusername=<username> pn_clipassword=<password> pn_command='trunk-delete' pn_name='ansible-trunk'
    register: cmd_output
  - debug: var=cmd_output
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| command | The CLI command run on target nodes. | always | string |
| stdout | Output of the CLI command. | on success | string |
| stderr | Error message from the CLI command. | on failure | string |
| changed | Indicates whether the CLI caused changes in the target node.| always | bool |
