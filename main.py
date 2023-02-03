#!/usr/bin/python3

import uuid
import time
from os import chmod


def cleanup(client, log, pylxd):
    instances_to_delete = [i for i in client.instances.all()
                           if i.description == 'test']

    for i in instances_to_delete:
        try:
            i.stop(wait=True)
        except pylxd.exceptions.LXDAPIException as lxdapi_exception:
            if str(lxdapi_exception) == 'The instance is already stopped':
                pass
            else:
                log.info(lxdapi_exception)
                exit(1)
        i.delete(wait=True)
        log.info(i.name + ' deleted')


def create_keypair(RSA):
    '''
    creates ssh keypair for use with ansible
    returns public key
    '''
    key = RSA.generate(4096)
    with open("./private.key", 'wb') as content_file:
        chmod("./private.key", 0o600)
        content_file.write(key.exportKey('PEM'))
    pubkey = key.publickey()
    with open("./public.key", 'wb') as content_file:
        content_file.write(pubkey.exportKey('OpenSSH'))
    return pubkey


def create_node(client, name, image, pubkey, log):
    name = name + '-' + str(uuid.uuid4())[0:5]
    config = {'name': name,
              'description': 'test',
              'source': {'type': 'image',
                         'mode': 'pull',
                         'server': 'https://images.linuxcontainers.org',
                         'protocol': 'simplestreams',
                         'alias': image},
              'config': {'limits.cpu': '2',
                         'limits.memory': '1GB'}}
    log.info('creating node ' + name)
    inst = client.instances.create(config, wait=True)
    inst.start(wait=True)
    wait_until_ready(inst, log)

    if 'rocky' in image:
        pkgm = 'yum'
    elif 'debian' or 'ubuntu' in image:
        pkgm = 'apt'

    err = inst.execute([pkgm, 'install', 'python3', 'openssh-server', 'ca-certificates', '-y'])
    log.info(err.stdout)
    if err.exit_code != 0:
        log.info(err.stderr)
        exit(1)
    err = inst.execute(['mkdir', '-p', '/root/.ssh'])
    log.info(err.stdout)
    if err.exit_code != 0:
        log.info('failed to mkdir /root/.ssh')
        log.info(err.stderr)
        exit(1)

    inst.files.put('/root/.ssh/authorized_keys', pubkey.exportKey('OpenSSH'))
    # wow! subsequent reboots in network configuration were borking our ssh installation/configuration
    inst.execute(['sync'])
    return inst


def wait_until_ready(instance, log):
    '''
    waits until an instance is executable
    '''
    log.info('waiting for lxd agent to become ready on ' + instance.name)
    count = 30
    for i in range(count):
        if instance.execute(['hostname']).exit_code == 0:
            break
        if i == count - 1:
            log.info('timed out waiting')
            exit(1)
        time.sleep(1)


if __name__ == '__main__':
    def main():
        import pylxd
        from pylxd import models # noqa
        import ansible_runner
        from ansible_runner.display_callback.callback import awx_display # noqa
        import logging
        import argparse
        from Crypto.PublicKey import RSA

        logging.basicConfig(format='%(funcName)s(): %(message)s')
        log = logging.getLogger(__name__)
        log.setLevel(logging.INFO)
        client = pylxd.Client()

        parser = argparse.ArgumentParser()
        parser.add_argument('--create', action='store_true')
        parser.add_argument('--preserve', action='store_true')
        parser.add_argument('--cleanup', action='store_true')
        parser.add_argument('--image', type=str, default='debian/12')
        args = parser.parse_args()

        if args.cleanup:
            cleanup(client, log, pylxd)
        elif args.create:
            pubkey = create_keypair(RSA)
            inst = create_node(client, 'test', args.image, pubkey, log)

            ansible_hostname = inst.state().network['eth0']['addresses'][0]['address']
            inventory = '{} ansible_ssh_private_key_file=private.key ansible_user=root'.format(ansible_hostname)

            with open('test.inventory', 'w') as f:
                f.truncate()
                f.write(inventory)

            playbook = '''---
- hosts: all
  tasks:
    - ansible.builtin.include_vars:
        file: vars.yml
    - import_tasks: tasks/main.yml
  handlers:
    - import_tasks: handlers/main.yml
  vars:
    - ansible_host_key_checking: false
'''

            with open('main.yml', mode='w') as f:
                print(playbook, file=f)

            ansible_runner.run(
                private_data_dir='./',
                inventory='test.inventory',
                playbook='main.yml'
            )

            if args.preserve:
                log.info('environment created.  follow-up configuration can be performed with:')
                print('ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook main.yml -i test.inventory')
            else:
                cleanup(client, log, pylxd)

    main()
