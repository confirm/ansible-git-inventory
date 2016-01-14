# Description

This is a dynamic inventory script for Ansible and the Ansible Tower.
It reads hosts and groups from a git repositories' YAML file and "magically" transforms them into a dynamic inventory source for Ansible or the Ansible Tower API.

It has a few advantages over the static definition of hosts / groups in the Tower:

* hosts and groups can be maintained directly in git next to the Ansible plays/roles/variables
* host/group changes will be tagged together with the rest in the git repo
* management of complex host/group structures get simplified
* better overview thanks to the YAML instead of the WebUI

The provided YAML has a predefined layout, which is required for the scripts "magic" host group algorithm. Here's an example of a YAML file called `prod.yml`:

```yml
---
web:
    site1:
        - web1
        - web2
    site2:
        - web3
        - web4
db:
    site1:
        - db1
        - db2
    site2:
        - db3
        - db4
```

When the YAML file is parsed by the script, you'll have access to several host groups:

* __tier groups__ like `web`, `db`:
* __location groups__ like `site1`, `site2`:
* __tier-location groups__ like `web-site1`, `web-site2`, `db-site1`, `db-site2`

Because the file name is based on the environment, for example `prod.yml`, you also have access to environment based host groups:

* __env groups__ like `prod`
* __env-tier groups__ like `prod-web`, `prod-db`
* __env-location groups__ like `prod-site1`, `prod-site2`
* __env-tier-location groups__ like `prod-web-site1`, `prod-web-site2`, `prod-db-site1`, `prod-db-site2`

# Installation

## Ansible stand-alone script

* Download a relase from this repository.
* Install the requirements by executing

```
pip install -r requirements.txt
```

## Ansible Tower (one-time)

* Browse to the Ansible Tower WebUI
* Login as an user with administration privileges
* Click on the Administration icon on the upper right corner
* Click on the _Inventory Scripts_ link
* Create a new _Inventory Script_ by clicking on the + icon
* Drag n' drop or copy-paste this script into the text field
* Fill out the rest of the form and click _Save_

# Configuration

## Configure Tower Inventory

* Open an existing inventory in the Ansible Tower WebUI
* Create a new group by clicking the plus icon
* Enter a _name_ for the new (parent) group (e.g. _dynamic_)
* Click on the Source tab
* Select the custom script you've created in the last step

Please note you can / must set the following environment variables:

* `URL`: URL of the git repository, __mandatory__
* `INVENTORY`: Path of the inventory file, __mandatory__
* `SSHKEY`: Path to an alternate SSH key, optional
* `COMMIT`: Commit to checkout (i.e. branch or tag), optional
