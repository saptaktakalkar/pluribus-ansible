# pn_switch_config_reset

  This module can be used to perform a `switch-config-reset` to clear all the configurations on a switch.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to perform a `switch-config-reset` on a switch to clear all the configurations. 

## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |


## Examples

```

---

# This task is to perform a switch config reset on all the switches listed under hosts
# It uses pn_switch_config_reset module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml.
- name: Switch Config Reset
  hosts: all

  vars_files:
  - cli_vault.yml

  tasks:
    - name: Reset all switches
      pn_switch_config_reset:
        pn_cliusername: "{{ USERNAME }}"  # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"  # Cli password (value comes from cli_vault.yml).
      register: reset_out                 # Variable to hold/register output of the above tasks.

    - debug:
        var: reset_out.stdout_lines
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
