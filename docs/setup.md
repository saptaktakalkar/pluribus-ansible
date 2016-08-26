This document aims to help you get started with Pluribus Ansible and provides some tips to make the most of your ansible experience.
Ansible also has a comprehensive official documentation which is [amazing](#http://docs.ansible.com/ansible/index.html)!. You can refer it for more information. 

## Setup

```
  $ sudo apt-add-repository ppa:ansible/ansible -y                     
  $ sudo apt-get update && sudo apt-get install ansible -y
```
This will install ansible on your machine. To begin using pluribus-ansible modules or develop modules for pluribus-ansible, clone this repository in your ansible directory.

```
~$ cd /etc/ansible
~:/etc/ansible$ git clone <url>
~:/etc/ansible$ cd pluribus-ansible
~:/etc/ansible/pluribus-ansible$ git checkout -b <your branch>
```

Now you can begin working on your branch.

#NOTE: 
Checklist:
  1. Make sure you set the library path to point to your library directory in the `ansible.cfg` file.
  2. Disable host key checking in `ansible.cfg` file. If required, establish SSH keys.
  3. Make any required configuration changes.
 
## Index
+ [Directory Layout](#directory-layout)
+ [Configuration File](#configuration-file)
+ [Inventory File](#inventory-file)
+ [Group and Host variables](#group-and-host-variables)
+ [Playbooks](#playbooks)
+ [Module Development](#modules)

# Directory Layout
  This section tries to explains a typical directory structure for organizing contents of your project.
  The top level of the directory would contain files and directories like:
```
  /path/to/ansible/
  |-main.yml
  |-hosts
  |-library/
   '--pn_show.py
  |-group_vars/
  |-host_vars/
  |-roles/
```
  `group_vars`, `host_vars`, `roles` provide scalability, reusability and better code organization.

# Configuration File
  Custom changes to the ansible workflow and how it behaves are made through the configuration file. If you installed ansible from a package manager, the `ansible.cfg` will be present in `/etc/ansible` directory. If it is not present, you can create one to override default settings. Although the default settings should be sufficient for most of the purposes, you may need to change some of the settings based on your requirements.
  The default configuration file can be found here: [ansible.cfg](../ansible.cfg)

  Changes in relation to configuration are processed and picked up in the the following order:
```
  1. * ANSIBLE_CONFIG (an environment variable)
  2. * ansible.cfg (in the current directory)
  3. * .ansible.cfg (in the home directory)
  4. * .ansible.cfg (in /etc/ansible/ansible.cfg)
```
  An example directive from the config file:
```
  #inventory = /etc/ansible/hosts
```
  This line is to assign a different directory for a custom hosts file location. Remember to remove the `#` symbol to uncomment.

# Inventory File
  Inventory is a list of hosts, assembled into groups, on which you will run your ansible playbooks. Ansible works against multiple hosts in your infrastructure simultaneously. It does this by selecting a group of hosts listed in Ansible’s inventory file. Ansible has a default inventory file used to define which hosts it will be managing. After installation, there's an example one you can reference at `/etc/ansible/hosts`.
  Copy and move the default [hosts]() file for reference:
```
  $ sudo mv /etc/ansible/hosts /etc/ansible/hosts.orig
  $ sudo vim /etc/ansible/hosts
```
  Note: You can place the `hosts` file in your current working directory and change the inventory path in the `ansible.cfg` file.

  Here is an example of inventory file located in the ansible working directory ~/ansible/hosts
```
  mail.example.com

  [webservers]
  foo.example.com
  bar.example.com

  [dbservers]
  serverone.example.com
  servertwo.example.com
  serverthree.example.com
```
  Ansible automatically puts all the hosts in a group called **`all`**.
  Group names are enclosed in brackets `[]` and are used to classify hosts based on purpose.
  A host can be a part of multiple groups or none. There can be multiple inventory files and they can also be dynamic.
  Please refer: [Ansible-Inventory](https://docs.ansible.com/ansible/intro_inventory.html) for more on this.

# Group and Host variables
  Ansible allows you to have different inventory files for different environments. These inventory files contain various host classified into different groups based on environment, geographic location, scope etc. These groups and hosts can be associated with variables relative to the inventory file. Please refer: [Ansible-vars] (http://docs.ansible.com/ansible/playbooks_best_practices.html#how-to-differentiate-staging-vs-production) for more on this.

# Roles
  Roles are a way to automatically load certain vars_files, tasks and handlers based on the file structure. Roles are good for organizing multiple, related Tasks and encapsulating data needed to accomplish those Tasks. A role contains various optional directories besides `tasks` and each sub-directory contains an entrypoint `main.yml`. The other directories can be handlers, defaults, templates and files.

  - `tasks`: You can include a list of tasks that you would implement across different plays and playbooks in `tasks/main.yml` and include them in your main playbook using `include` directive.
  - `handlers`: A handler is exactly similar to Task, but it will run only when called by another task(similar to an event system). This is useful to run secondary tasks that might be required after running a task. Ths is achieved using the `notify` directive in the parent task.
  - `defaults`: This contains defaults for variables used in the roles.
  - `files`:
  - `templates`:

# Modules
  Ansible modules are reusable piece of code that can be invoked using the ansible API or through the Ansible playbook. Although Ansible modules can be written in any language, Python is the preferred choice. The Ansible module should be capable of handling different arguments, return statuses, errors and failures. This can be achieved by the **AnsibleModule** boilerplate which provides an efficient way to handle arguments and return statuses.

## AnsibleModule boilerplate
  All you need to do is import `ansible.module_utils.basic`
  Put the import function at the end of your file and include your actual module body inside the conventional `main` function.
```
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
```

  Module class can be instantiated as follows:
```
def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            something = dict(aliases=['whatever'])
        )
    )
```
  As you can see, the **AnsibleModule** boilerplate allows you to specify if the arguments are optional or required, set default values. It also handles different data types.

##  Interaction between parameters:
   The **AnsibleModule** boilerplate also offers interaction between the arguments. It allows you to specify if certain arguments are mutually exclusive or required together. An argument can be `required` or `optional`. You can set `default` values to optional arguments. Also, the possible inputs to a particular argument can be restricted using `choice` keyword.
```
    module = AnsibleModule(
        argument_spec=dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            something = dict(aliases=['whatever']),
            argument1 = dict(type='str'),
            argument2 = dict(type='str')
        ),
        mutually_exclusive=[
            [ "argument1", "argument2"]
        ],
        required_together=[
            [ "name", "state"]
        ],
        required_one_of=dict=[
            ["state", "something"]
        ],
        required_if=[
            ["state", "present", ["enabled", "argument1", "something"],
            ["state", "absent", ["enabled", "argument2"]
        ]
    )
```
  `mutually_exclusive` - takes a list of lists and ech embedded list consists of parameters which cannot appear together.
  `required_together` - all the specified parameters are required together
  `required_one_of` - at least one of the specified parameters is required
  `required_if` - it checks the value of one parameter and if that value matches, it requires the specified parameters to be present as well.

##  Accessing the arguments:
   Ansible provides an easy way to access arguments from the module instance.
```
    state = module.params['state']
    name = module.params['name']
    enabled = module.params['enable']
    something = module.params['something']
    argument1 = module.params['argument1']
    argument2 = module.params['argument2']
```

  Modules must output valid JSON. **AnsibleModule** boilerplate has a common function, `module.exit_json` for JSON format output. Successful returns are made using:
```
    module.exit_jason(
        changed = True,
        stdout = response
    )

    or

    module.exit_json(
        changed = False,
        stdout = response
    )
```
  Failures are handled in a similar way:
```
    module.fail_json(
        changed = False,
        msg="Something Failed!"
     )
```

##  Documentation:
   All modules must be documented. The modules must include a `DOCUMENTATION` string. This string must be a valid **YAML** document.
```
    #!/usr/bin/python
    # Copyright/License header

    DOCUMENTATION = '''
    ---
    module: modulename
    short_description: A sentence describing the module
    # ... snip...
    '''
```

  The description field supports formatting functions such as `U()`, `M()`, `I()` and `C()` for URL, module, italics and constant width respectively. It is suggested to use `C()` for file and option names, `I()` when referencing parameters, and `M()` for module names.

##  Examples:
   Example section must be written in plain text in an `EXAMPLES` string within the module.

```
    EXAMPLES = '''
    - action: modulename opt1=arg1 opt2=arg2
```

##  Return:
   The `RETURN` section documents what the module returns. For each returned value, provide a `description`, in what circumstances the value is `returned`, the `type` of the value and a `sample`.
```
    RETURN = '''
    - return_value:
        description: short description for the returned value
        returned:
        type:
        sample:
    '''
```

# Playbooks
   The real strength of Ansible lies in Playbooks. A playbook is like a recipe or instruction manual which tells ansible what to do when it connects to each machine. Playbooks are expressed in YAML format and have a minimum of syntax. Each playbook is composed of one or more plays. The goal of a play is to map a group of hosts to some well defined tasks. A task is basically a call to ansible module. The good thing about playbooks is that there is no defined format, you can write a playbook in different ways. You can organize plays, tasks in different ways. You can also add modularity with the help of `roles`. 
     
  Here is an example of a playbook to run `vlan-show`:
```
    ---
    - name: "This Playbook is to view Vlan configurations."
      hosts: spine
      user: network-admin
      
      tasks:
      - pn_show: username=network-admin password=admin pn_showcommand=vlan-show pn_showformat=switch,id,desc pn_quiet=True
      register: vlan_show_output
      - debug: var:vlan_show_output
```

   A few things to note:

   - Nearly every YAML file starts with a list. Each item in the list is a list of key/value pairs, commonly called a “hash” or a “dictionary”.
   - All YAML files can optionally begin with `---` and end with `...`. This is part of the YAML format and indicates the start and end of a document.
   - It is possible to leave off the ‘name’ for a given task, though it is recommended to provide a description about why something is being done instead. This name is shown when the playbook is run.
   - Generous use of whitespace to break things up, and use of comments (which start with ‘#’), is encouraged.
   - All members of a list are lines beginning at the same indentation level starting with a `- ` (a dash and a space).
   - [YAML Lint](#http://www.yamllint.com/) can help you debug YAML syntax.
## The Following Modules are supported right now:
   - LAG
   - vLAG
   - VLAN
   - Port Configuration
   - vRouters
   - VRRP
   - BGP
   - OSPF
   - Pluribus CLI as a parameter (allows to configure any new feature)

   
   The official [Ansible doc](#http://docs.ansible.com/ansible/playbooks.html) provides more information on Playbooks and YAML. 
