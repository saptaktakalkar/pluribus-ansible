#!/usr/bin/python
""" PN-CLI module for fabric-create/fabric-join"""
import shlex
import subprocess


def main():
    """Module instantiation"""
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_fabric_command=dict(required=True, type='str',
                                   choices=["fabric-create", "fabric-join"]),
            pn_fabric_name=dict(required=True, type='str')
        )
    )

    # Accessing arguments
    cliusername = module.params["pn_cliusername"]
    clipassword = module.params["pn_clipassword"]
    fabric_command = module.params["pn_fabric_command"]
    fabric_name = module.params["pn_fabric_name"]

    # Building the CLI
    fabric = ('/usr/bin/cli --user ' + cliusername + ':' + clipassword +
              ' ' + fabric_command + ' ' + fabric_name)
    # Running the CLI
    command = shlex.split(fabric)
    response = subprocess.Popen(command, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if err:
        module.exit_json(
            command=fabric,
            stderr=err.rstrip("\r\n"),
            changed=False
        )
    else:
        module.exit_json(
            command=fabric,
            stdout=out.rstrip("\r\n"),
            changed=True
        )
# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
