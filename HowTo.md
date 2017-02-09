### Run playbooks

#### Switch-Config-Reset Playbook

```
# ansible-playbook -i hosts pn_switch_reset.yml -u pluribus --ask-pass --ask-vault-pass -K
```

```
--snip--
PLAY [Switch Config Reset] *****************************************************

TASK [setup] *******************************************************************
ok: [ansible-leaf2]
ok: [ansible-leaf3]
ok: [ansible-leaf1]
ok: [ansible-spine2]
ok: [ansible-spine1]
ok: [ansible-leaf4]

TASK [Reset all switches] ******************************************************
ok: [ansible-leaf3]
ok: [ansible-leaf2]
ok: [ansible-leaf1]
ok: [ansible-spine1]
ok: [ansible-spine2]
ok: [ansible-leaf4]
.
.
PLAY RECAP *********************************************************************
ansible-leaf1              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf2              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf3              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf4              : ok=3    changed=0    unreachable=0    failed=0
ansible-spine1             : ok=4    changed=0    unreachable=0    failed=0
ansible-spine2             : ok=3    changed=0    unreachable=0    failed=0
--snip--
```

#### Fabric Playbook

```
# ansible-playbook -i hosts pn_fabric.yml -u pluribus --ask-pass --ask-vault-pass -K
```

```
--snip--
PLAY [Zero Touch Provisioning - Initial setup] *********************************

TASK [setup] *******************************************************************
ok: [ansible-spine1]

TASK [Auto accept EULA, Disable STP, enable ports and create/join fabric] ******
changed: [ansible-spine1]

TASK [debug] *******************************************************************
ok: [ansible-spine1] => {
    "ztp_out.stdout_lines": [
        "  EULA has been accepted already!  ansible-spine1 is already in fabric vcf-ansible-fab!  Fabric is already in mgmt control network  STP is already disabled!  Ports enabled on ansible-spine1! "
    ]
}
.
.
PLAY RECAP *********************************************************************
ansible-leaf1              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf2              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf3              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf4              : ok=4    changed=1    unreachable=0    failed=0
ansible-spine1             : ok=4    changed=1    unreachable=0    failed=0
ansible-spine2             : ok=4    changed=1    unreachable=0    failed=0
--snip--
