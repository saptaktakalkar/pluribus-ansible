# pn_cluster

Module for CLI cluster configurations. Supports `cluster-create`  and `cluster-delete` commands with options. 

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis
  
  A cluster allows two switches to cooperate in high-availability (HA) deployments. The nodes that
  form the cluster must be members of the same fabric. Clusters are typically used in conjunction
  with a virtual link aggregation group (VLAG) that allows links physically connected to two
  separate switches appear as a single trunk to a third device. The third device can be a switch,
  server, or any Ethernet device. 
  
 
 **_Informational Note_**: You may configure multiple clusters of switches within a single fabric. However,
    a switch can participate in only one cluster configuration. For example, switch-1 and switch-2 can
    participate in cluster-1, and switch-3 and switch-4 can participate in cluster-2, but switch-1 and
    switch-2 cannot participate in cluster-2 or any other cluster. 


## Options

| parameter       | required       | default      | type         | choices       | comments                                                   |
|-----------------|----------------|--------------|--------------|----------------------------------------------------------------------------|
|pn_cliusername   | see comments   |              | str          |               | Provide login username if user is not root.                |
|pn_clipassword   | see comments   |              | str          |               | Provide login password if user is not root                 |
|pn_cliswitch     | no             | local        | str          |               | Target switch(es) to run command on.                       |
|pn_command       | yes            |              | str          | cluster-create, cluster-delete| Create or delete cluster configuration.    |
|pn_name          | yes            |              | str          |               | Specify the name of the cluster.                           |
|pn_cluster_node1 | for cluster-create    |       | str          |               | Specify the name of the first switch in the cluster.       |
|pn_cluster_node2 | for cluster-create    |       | str          |               | Specify the name of the second switch in the cluster.      |
|pn_validate      | no             |              | bool         |               | Validate the inter-switch links and state of the switches in the cluster. |


## Usage

```
- name: "Playbook for CLI Cluster"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN cluster command"
    pn_cluster: > 
     [pn_cliusername=<username>] 
     [pn_clipassword=<password>]
     pn_command=<cluster-create/delete> 
     pn_name=<cluster name>  
     [pn_cluster_node1=<cluster-node-1>] 
     [pn_cluster_node2=<cluster-node-2>] 
     [pn_validate=<validate|no-validate>] 
     [pn_quiet=<True/False>]
  
```

## Examples

# cluster-create
Sample playbook for **_creating_** a Cluster configuration with `user: pluribus`.

```
---
- name: "Playbook for Cluster Create"
  hosts: spine[0]
  user: pluribus
  tasks:
  - name: "Create spine cluster"
    pn_cluster: >
      pn_cliusername=<username> 
      pn_clipassword=<password>
      pn_command=cluster-create 
      pn_name=spine-cluster 
      pn_cluster_node1=spine01 
      pn_cluster_node2=spine02 
      pn_validate=validate 
      pn_quiet=True
    register: cmd_output
  - debug: var=cmd_output
  
```


# cluster-delete
Sampe Playbook for **_deleting_** a Cluster Configuration with `user: root`.

```
---
- name: "Playbook for Cluster Delete"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Delete spine cluster"
    pn_cluster:
      pn_command=cluster-delete 
      pn_name=spine-cluster 
      pn_quiet=True
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
