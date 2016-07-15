#!/usr/bin/python
""" PN CLI cluster-create/cluster-delete """

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_cluster
author: "Pluribus Networks"
short_description: CLI command to create/delete a cluster
description:
  - Execute cluster-create or cluster-delete command. 
  - Requires cluster name:
    - Alphanumeric characters
    - Special characters like: _
options:
  pn_cliusername:
    description:
      - Login username
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password
    required: true
    type: str
  pn_clustercommand:
    description:
      - The C(pn_clustercommand) takes the cluster-create/cluster-delete command
      as value.
    required: true
    choices: cluster-create, cluster-delete
    type: str
  pn_clustername:
    description:
      - The C(pn_clustername) takes a valid name for cluster configuration.
    required: true
    type: str
  pn_clusternode1:
    description:
      - name for cluster-node 1
    required_if: cluster-create 
    type: str
  pn_clusternode2:
    description:
      - name for cluster-node 2
    required_if: cluster-create
    type: str
  pn_clustervalidate:
    description:
      - validate the cluster link
    required: false
    choices: validate, no-validate
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create spine cluster
  pn_cluster:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_clustercommand: 'cluster-create'
    pn_clustername: 'spine-cluster'
    pn_clusternode1: 'spine01'
    pn_clusternode2: 'spine02'
    pn_clustervalidate: True
    pn_quiet: True

- name: delete spine cluster
  pn_cluster:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_clustercommand: 'cluster-delete'
    pn_clustername: 'spine-cluster'
    pn_quiet: True
"""

RETURN = """
clustercmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the cluster command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
  returned: always
  type: list
stderr:
  description: the set of error responses from the cluster command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_clustercommand=dict(required=True, type='str',
                                   choices=['cluster-create',
                                            'cluster-delete']),
            pn_clustername=dict(required=True, type='str'),
            pn_clusternode1=dict(type='str'),
            pn_clusternode2=dict(type='str'),
            pn_clustervalidate=dict(required=False, type='str',
                                    choices=['validate', 'no-validate']),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_clustercommand", "cluster-create",
             ["pn_clustername", "pn_clusternode1", "pn_clusternode2"]],
            ["pn_clustercommand", "cluster-delete", ["pn_clustername"]]
        )
    )

    # Accessing the parameters
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    clustercommand = module.params['pn_clustercommand']
    clustername = module.params['pn_clustername']
    clusternode1 = module.params['pn_clusternode1']
    clusternode2 = module.params['pn_clusternode2']
    clustervalidate = module.params['pn_clustervalidate']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    if clustername:
        cli += clustercommand + ' name ' + clustername

    if clusternode1:
        cli += ' cluster-node-1 ' + clusternode1

    if clusternode2:
        cli += ' cluster-node-2 ' + clusternode2

    if clustervalidate:
        cli += ' ' + clustervalidate

    # Run the CLI command
    clustercmd = shlex.split(cli)
    response = subprocess.Popen(clustercmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    # Response in JSON format
    if out:
        module.exit_json(
            command=cli,
            stdout=out.rstrip("\r\n"),
            changed=True
        )

    if err:
        module.exit_json(
            command=cli,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
