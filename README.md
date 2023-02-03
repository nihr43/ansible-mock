# ansible-mock

Develop and test Ansible roles on the fly with LXD containers.

## usage

From within a role directory, this tool will:

- create an lxd container of `--image`
- generate and land a root ssh key
- generate a playbook `main.yml` that enters your role at tasks/main.yml
- execute the playbook

A role is expected to be laid out as follows.  vars.yml contains default vars if any:

```
.
├── handlers
├── tasks
├── templates
└── vars.yml
```

To run the role:

```
$ ansible-mock --create
create_node(): creating node test-46b9b
wait_until_ready(): waiting for lxd agent to become ready on test-46b9b
create_node(): Reading package lists...
Building dependency tree...
Reading state information...
The following additional packages will be installed:
...
create_node(): 
 ____________
< PLAY [all] >
 ------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
 ________________________
< TASK [Gathering Facts] >
 ------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
ok: [10.139.0.5]
 _____________________________________
< TASK [ansible.builtin.include_vars] >
 -------------------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
ok: [10.139.0.5]
 _____________________________
< TASK [Enforce ssh key auth] >
 -----------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
changed: [10.139.0.5]
 _______________________________
< TASK [Disable sshd passwords] >
 -------------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
changed: [10.139.0.5]
...
10.139.0.5                 : ok=11   changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1   
cleanup(): test-46b9b deleted
```

By default, the instance is immediately deleted.

If used with `--preserve`, ansible-mock leaves behind the inventory, playbook, and key to run subsequent `ansible-playbook` commands without having to recreate everything:

```
ansible-mock --create --preserve
create_node(): creating node test-50767
wait_until_ready(): waiting for lxd agent to become ready on test-50767
...
main(): environment created.  follow-up configuration can be performed with:
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook main.yml -i test.inventory
```

You can then run:

```
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook main.yml -i test.inventory
```
