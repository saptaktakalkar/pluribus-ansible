# pn_vlan

 Module for CLI vlan configurations. Supports `vlan-create`, `vlan-delete` and `vlan-modify` commands with options. 


 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  VLANs are used to isolate network traffic at Layer 2. The VLAN identifiers 0 and 4095 are reserved and cannot be used per the IEEE 802.1Q standard. The range of configurable VLAN identifiers is 2 through 4092.
  For a complete discussion of all the features, please refer to the Pluribus Networks technical product documentation.
      
## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_cliswitch     | no             | local         | str         |               | Target switch(es) to run command on.                       |
| pn_command       | yes            |               | str         | vlan-create, vlan-delete, vlan-modify | Create, delete or modify VLANs.   |
| pn_vlanid        | yes            |               | int         |               | Specify a VLAN identifier for the VLAN. This is a value between 2 and 4092.|
| pn_scope         | for vlan-create|               | str         | fabric, local | Specify a scope for the VLAN.                              |
| pn_description   | no             |               | str         |               | Provide a description for the vlan.                        |
| pn_stats         | no             |               | bool        | True, False   | Enable/disable statistics collection for the VLAN.       |
| pn_ports         | no             |               | str         |               | Specifies the switch network data port number, list of ports, or range of ports. Port numbers must ne in the range of 1 to 64.|
| pn_untagged_ports| no             |               | str         |               | Specifies the ports that should have untagged packets mapped to the VLAN. Untagged packets are packets that do not contain IEEE 802.1Q VLAN tags.|


## Usage

```
- name: "Playbook for CLI VLAN"
  hosts: <hosts>
  user: <user>
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: PN VLAN command
    pn_vlan: >
      [pn_cliusername: <username>]
      [pn_clipassword: <password>]
      pn_command: <vlan-create/vlan-delete> 
      pn_vlanid: <vlan-id> 
      [pn_scope: <fabric/local>]
  
```

## Examples

# vlan-create
Sample playbook for **_creating_** a VLAN configuration with `user: pluribus`.

Equivalent CLI:
```
CLI......> vlan-create id 254 scope fabric
```


```
---
- name: Playbook for VLAN Create
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: Create VLAN
    pn_vlan: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}" 
      pn_command: vlan-create 
      pn_vlanid: 254 
      pn_scope: fabric
    register: cmd_output
  - debug: var=cmd_output
  
```

Sample playbook for **_creating_** multiple VLAN configurations with `user: pluribus`.

Equivalent CLI:
```
CLI......> vlan-create id 201 scope fabric
CLI......> vlan-create id 1024 scope local
CLI......> vlan-create id 355 scope fabric
```

```
---
- name: Playbook for VLAN Create
  hosts: spine[0]
  user: pluribus
  
  tasks:
  - name: Create VLANs 
    pn_vlan: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}"
      pn_command: vlan-create 
      pn_vlanid: "{{ item.id }}" 
      pn_scope: "{{ item.scope }}"
    with_items:
    - { id: 201, scope: 'fabric' }
    - { id: 1024, scope: 'local' }
    - { id: 355, scope: 'fabric' }
    register: cmd_output
  - debug: var=cmd_output
  
```

# vlan-delete
Sample playbook for **_deleting_** VLAN configurations with `user: root`.

Equivalent CLI:
```
CLI......> vlan-delete id 254
CLI......> vlan-delete id 201
CLI......> vlan-delete id 1024
CLI......> vlan-delete id 355

```

```
---
- name: Playbook for VLAN Delete
  hosts: spine[0]
  user: root
  
  tasks:
  - name: Delete VLANs
    pn_vlan: 
      pn_command: vlan-delete  
      pn_vlanid: "{{ item }}" 
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
