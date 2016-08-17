# pn_vrouter

 Module for CLI vrouter configurations. Supports `vrouter-create`, `vrouter-delete` and `vrouter-modify` commands with options.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  Each fabric, cluster, standalone switch, or virtual network (VNET) can provide its tenants with a virtual router (vRouter) service that forwards traffic between networks and implements Layer 3 protocols.
  For a complete discussion of all the features, please refer to the Pluribus Networks technical product documentation.
  
## Options

| parameter       | required       | default       | type        | choices       | comments                                                   |
|-----------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername  | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword  | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_cliswitch    | no             | local         | str         |               | Target switch(es) to run command on.                       |
| pn_command      | yes            |               | str         | vrouter-create, vrouter-delete, vrouter-modify | Create, delete, modify vrouter configurations.|
| pn_name         | yes            |               | str         |               | Specify the name of the vRouter.                           |
| pn_vnet         | for vrouter-create |           | str         |               | Specify the name of the VNET.(Usually fabric name appended with '-global') |
| pn_service_type | no             |               | str         | dedicated, shared | Specify if the vRouter is a dedicated or a shared VNET service.| 
| pn_service_state| no             |               | str         | enable, disable| Specify to enable disable vRouter service.               |
| pn_router_type  | no             |               | str         | hardware, software | Specify if the vRouter uses software or hardware.    |
| pn_hw_vrrp_id   | no             |               | int         |               | Specifies the VRRP ID for a hardware vrouter.              |
| pn_router_id    | no             |               | str         |               | Specify the vRouter IP address.                            |
| pn_bgp_as       | no             |               | int         |               | Specify the Autonomous System number if the vRouter runs BGP. This is a number between 1 to 4294967295.|
| pn_bgp_redistribute | no         |               | str         | static, connected, rip, ospf | Specify how BGP routes are redistributed.  |
| pn_bgp_max_paths| no             |               | int         |               | Specify the maximum number of paths for BGP. This is a number between 1 and 255 or 0 to unset. |
| pn_bgp_options  | no             |               | str         |               | Specify other BGP options as a whitespace separated string within single quotes. |
| pn_rip_redistribute | no         |               | str         | static, connected, ospf, bgp | Specify how RIP routes are redistributed.  |
| pn_ospf_redistribute | no        |               | str         | static, connected, rip, bgp | Specify how OSPF routes are redistributed.  |
| pn_ospf_options | no             |               | str         |              | Specify other OSPF options as a whitespace separated string within single quotes. |



**NOTE**: If you specify hardware as router type, you cannot assign IP address using DHCP. You must specify a static IP address.

## Usage

```
- name: "Playbook for CLI vrouter"
  hosts: <hosts>
  user: <user>
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: "PN vrouter command"
    pn_vrouter: >
      [pn_cliusername: <username>] 
      [pn_clipassword: <password>] 
      pn_command: <vrouter-create/delete/modify> 
      pn_name: <name> 
      [pn_vnet] 
      [pn_service_state: <enable/disable>] 
      [pn_hw_vrrp_id: <hw vrrp id>] 
      [pn_bgp_as: <bgp as number>] 
      [pn_quiet: <True/False>]
  
```

## Examples

# vrouter-create
Sample playbook for **_creating_** a vRouter configuration with `user: pluribus`.

Equivalent CLI:
```
CLI......> vrouter-create name ansible-vrouter vnet ansible-vnet-global service-state enable hw-vrrp-id 18
```

```
---
- name: "Playbook for vrouter Create"
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: "Create vrouter"
    pn_vrouter: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}"
      pn_command: vrouter-create 
      pn_name: ansible-vrouter 
      pn_vnet: ansible-vnet-global 
      pn_service_state: enable 
      pn_hw_vrrp_id: 18
    register: cmd_output
  - debug: var=cmd_output
  
```

# vrouter-delete
Sample playbook for **_deleting_** a vrouter configuration with `user: root`.

Equivalent CLI:
```
CLI......> vrouter-delete name ansible-vrouter
```

```
---
- name: "Playbook for vrouter Delete"
  hosts: spine[0]
  user: root
  
  tasks:
  - name: "Delete vrouter"
    pn_vrouter: 
      pn_command: vrouter-delete 
      pn_name: ansible-vrouter
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
