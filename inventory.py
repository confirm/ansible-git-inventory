#!/usr/bin/env python
import os
import sys
import yaml
import json
import re
from subprocess import check_call
from argparse import ArgumentParser
from tempfile import mkdtemp
from shutil import rmtree


class AnsibleGitInventory(object):
    '''
    Class to read a YAML from a git repository and generate a valid Ansible
    dynamic inventory output.

    Please use this class within a with-block or call the cleanup() method
    manually when you're finished.
    '''

    def __init__(self):
        '''
        Class constructor which creates the temporary working directory.
        '''
        self.working_dir = mkdtemp()

    def __enter__(self):
        '''
        Returns the instance pointer when with-context is entered.
        '''
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''
        Wrapper to call cleanup() when with-context is exited.
        '''
        self.cleanup()

    def cleanup(self):
        '''
        Removes the temporary working directory and therefor all generated
        data on the filesystem.
        '''
        if os.path.isdir(self.working_dir):
            rmtree(self.working_dir)

    def clone_repository(self, url, commit=None, sshkey=None):
        '''
        Clone git repository into a temporary working directory.

        To specify a specific commit branch or tag you can use the `commit`
        argument. If you want to use an alternative SSH key define the
        `sshkey` argument.
        '''
        if sshkey:
            os.environ['GIT_SSH_COMMAND'] = 'ssh -i ' + sshkey

        command = ['git', 'clone', '-q']

        if commit:
            command.extend(['-b', commit])

        command.append(url)
        command.append(self.working_dir)

        check_call(command)

    def parse_inventory(self, path):

        inventory = os.path.join(self.working_dir, path)
        name      = os.path.basename(inventory).split('.')[0]

        if not os.path.isfile(inventory):
            raise IOError('Inventory file "{}" not found in repository'.format(path))

        # Read inventory file.
        with open(inventory, 'r') as f:
            # Parse YAML.
            data = yaml.load(f)

            # Prepare result dict.
            result = {
                '_meta': {
                    'hostvars': {}
                },
                name: {
                    'children': []
                }
            }

            # Loop through inventory YAML and build result yaml.
            for tier, group in data.iteritems():

                # Build group name for inv-tier.
                inv_tier = '{0}-{1}'.format(name, tier)

                # Create empty tier & inv-tier groups.
                result[tier] = {
                    'children': []
                }
                result[inv_tier] = {
                    'children': [tier]
                }

                # Add tier to inv group.
                result[name]['children'].append(tier)

                for loc, hosts in group.iteritems():

                    # Build group names for tier-loc, inv-loc and inv-tier-loc.
                    tier_loc     = '{0}-{1}'.format(tier, loc)
                    inv_loc      = '{0}-{1}'.format(name, loc)
                    inv_tier_loc = '{0}-{1}'.format(name, tier_loc)

                    # Add tier-loc to tier group.
                    result[tier]['children'].append(tier_loc)

                    # Add tier-loc to inv-loc group.
                    if inv_loc not in result:
                        result[inv_loc] = {
                            'children': []
                        }
                    result[inv_loc]['children'].append(tier_loc)

                    # Add inv-loc to loc group.
                    if loc not in result:
                        result[loc] = {
                            'children': [inv_loc]
                        }
                    elif inv_loc not in result[loc]['children']:
                        result[loc]['children'].append(inv_loc)

                    # Create tier-loc and inv-tier-loc groups.
                    result[tier_loc] = {
                        'hosts': hosts
                    }
                    result[inv_tier_loc] = {
                        'children': [tier_loc]
                    }

            return json.dumps(obj=result, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':


    #
    # Get arguments from CLI or via environment variables.
    #
    # We need to do that because the Tower can't pass any CLI arguments to a
    # dynamic inventory script. Therefor environment variables must be used.
    #


    if 'URL' in os.environ and 'INVENTORY' in os.environ and os.environ['URL'] and os.environ['INVENTORY']:

        kwargs_clone = {
            'url': os.environ['URL'],
        }

        inventory = os.environ['INVENTORY']

        if 'SSHKEY' in os.environ:
            kwargs_clone['sshkey'] = os.environ['SSHKEY']

        if 'COMMIT' in os.environ:
            kwargs_clone['commit'] = os.environ['COMMIT']

    else:

        # Parse CLI arguments.
        parser = ArgumentParser(description='Ansible inventory script')
        parser.add_argument('--sshkey', help='Path to an alternative SSH private key', type=str)
        parser.add_argument('--commit', help='Commit to checkout (e.g. branch or tag)', type=str)
        parser.add_argument('url', help='URL of the git repository', type=str)
        parser.add_argument('inventory', help='Path of the inventory file', type=str)
        args = parser.parse_args()

        kwargs_clone = {
            'url': args.url,
            'sshkey': args.sshkey,
            'commit': args.commit,
        }

        inventory = args.inventory

    #
    # Clone repository and parse inventory file.
    #

    try:

        with AnsibleGitInventory() as obj:

            # Clone repository.
            obj.clone_repository(**kwargs_clone)

            # Parse inventory.
            data = obj.parse_inventory(path=inventory)

        # Print inventory JSON and exit.
        sys.stdout.write(data + '\n')
        sys.stdout.flush()
        sys.exit(0)

    except Exception, e:
        sys.stderr.write(str(e) + '\n')
        sys.stderr.flush()
        sys.exit(1)
