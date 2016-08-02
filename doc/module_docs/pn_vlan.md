# pn_vlan

 Module for CLI vlan configurations. Supports `vlan-create`, `vlan-delete` and `vlan-modify` commands with options. 

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  VLANs are used to isolate network traffic at Layer 2. The VLAN identifiers 0 and 4095 are reserved and cannot be used per the IEEE 802.1Q standard. The range of configurable VLAN identifiers is 2 through 4092.
  
## Options

| parameter       | required       | default      |choices       |comments                                                    |
|-----------------|----------------|--------------|--------------|------------------------------------------------------------|
| pn_cliusername  | yes            |              |              | Login username.                                            |
| pn_clipassword  | yes            |              |              | Login password.                                            |
| pn_cliswitch    | no             |              |              | Target switch(es) to run command on.                       |
| pn_command      | yes            |              | vlan-create, vlan-delete, vlan-modify | Create, delete or modify VLANs.   |
| pn_vlanid       | yes            |              |              | Specify a VLAN identifier for the VLAN. This is a value between 2 and 4092.|
| pn_scope        | for vlan-create|              | fabric, local| Specify a scope for the VLAN.                              |
| pn_description  | no             |              |              | Provide a description for the vlan.                        |
| pn_stats        | no             |              | stats, no-stats| Enable/disable statistics collection for the VLAN.       |
| pn_ports        | no             |              |              | Specifies the switch network data port number, list of ports, or range of ports. Port numbers must ne in the range of 1 to 64.|
| pn_untagged_ports| no            |              |              | Specifies the ports that should have untagged packets mapped to the VLAN. Untagged packets are packets that do not contain IEEE 802.1Q VLAN tags.|
| pn_quiet        | no             | true         |              | Enable/disable system information.                         |


## Usage

```
- name: "Playbook for CLI VLAN"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: PN VLAN command
    pn_vlan: >
      pn_cliusername=<username>
      pn_clipassword=<password>
      pn_command=<vlan-create/vlan-delete> 
      pn_vlanid=<vlan-id> 
      [pn_scope=<fabric/local>] 
      [pn_description=<description>] 
      [pn_stats=<stats/no-stats] 
      [pn_ports=<ports-list>] 
      [pn_untagged_ports=<untagged ports-list>] 
      [pn_quiet=<True/False>]
  
```

## Examples

# vlan-create
Sample playbook for **_creating_** a VLAN configuration.

```
---
- name: Playbook for VLAN Create
  hosts: spine[0]
  user: root
  tasks:
  - name: Create VLAN
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_command=vlan-create pn_vlanid=254 pn_scope=fabric
    register: cmd_output
  - debug: var=cmd_output
  
```

Sample playbook for **_creating_** multiple VLAN configurations.
```
---
- name: Playbook for VLAN Create
  hosts: spine[0]
  user: root
  tasks:
  - name: Create VLANs 
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_command=vlan-create pn_vlanid={{ item.id }} pn_scope={{ item.scope }}
    - { id: '201', scope: 'fabric' }
    - { id: '1024', scope: 'local' }
    - { id: '355', scope: 'fabric' }
    register: cmd_output
  - debug: var=cmd_output
  
```

# vlan-delete
Sample playbook for **_deleting_** VLAN configurations.

```
---
- name: Playbook for VLAN Delete
  hosts: spine[0]
  user: root
  tasks:
  - name: Delete VLANs
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_vlancommand=vlan-delete []() pn_vlanid={{ item }} pn_quiet=True 
    with_items:
    - 254
    - 201
    - 1024
    - 355
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
