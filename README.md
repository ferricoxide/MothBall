[![license](https://img.shields.io/github/license/plus3it/mothball.svg)](./LICENSE)
[![Build Status](https://travis-ci.org/plus3it/mothball.svg)](https://travis-ci.org/plus3it/mothball)

# Mothball
Mothball is a Python package and application primarily desiged to facilitate the medium- to long-term mothballing of a target AWS account. The Mothball package allows an operator to capture configuration data for an account and to convert AWS account-objects from higher (live) bill-states to lower (offline) bill-states. Mothballing allows an account to be converted to a mode that has a smaller periodic financial impact than if left either wholly live and running or even simply turned off. The capturing of configuration data and conversion of billable objects to lower-cost elements allows an account to be re-constituted to its former, full billing-footprint state without having to go through the exercise of completely rebuilding an account. The expected use-case for this suite of tools is AWS users who do periodic development and/or integration work within AWS but who have not yet fully-automated their cloud-layer and/or host-level provisioning procedures.

The idividual or process that executes this script will need to have sufficient AWS priviledges to:
- Collect configuration-information about all account objects
- Create EBS snapshots and similar storage-objects within the target account
- Initiate termination requests for all billable components that will be converted to lower bill-rate states
- Create and manage an RDS instance (if using a within-account configuration-collection RDS database)

## Installation

The Mothball tools rely primarily on AWS-layer privileges for use. The following installation instructions assume that the operator will execute the bulk of the Mothball-related actions through a standard user account. Root-level privileges should only be required for installing the tools to privileged system-locations (use of `sudo` is recommended for these tasks).

### For installation with Git from source.

This method may require the operator to update the interactive shell's PATH environmental variable in order to use the `MbBackup` command without invoking via explicitly-selected interpreter.

```
git clone https://github.com/plus3it/mothball.git
cd mothball
python setup.py build
sudo python setup.py install
```

### For for installation with pip

```
sudo pip install mothball
```

Validate that installation was successful and that the cli tool is available

```
MbBackup --help
```

## Configuration

Mothball requires a configuration file.  This file contains definitions for the database type and location, authentication information, and other necessary information for creating or using an RDS database instance to host preserved configuration data. This file may be located anywhere (`/usr/local/share/mothball/mothball.config` is just as valid as `${HOME}/mothball.config`) but should be owned by and only readable by the user/process executing mothball tasks.

**[Note: because this password is in cleartext, it is critical that the configuration file _only_ be readable by the user/process executing the mothball commands]**

The following is an example `mothball.config` file interspersed with explanatory text (the below is a single file):

~~~
    # Configurations for the Database to use.
    Database:
      # Supported Database types are MySQL and PostgreSQL
      type: mysql
    
      name: AWSBackup
    
      username: mothball
    
      password: mothballP4ssw0rd
~~~
The above parameters define:
- The type of database to connect to (or, in the case that an RDS is being created, the type of RDS-hosted database to launch): in this case, 'mysql'
- The datbase instance to create/use within the database service: in this case, the equivalent of logging into a MySQL DB and typing `use AWSbackup ;`
- The user with full rights on the named database instance: in this case, 'mothball'
- The clear-text password used by the user account to connect to the target database instance: in this case, 'mothballP4ssw0rd'
~~~
      # Host/Port only need to be defined if you are not using RDS and would 
      # rather back up to on an on prem or nonRDS db
      host:
      port: 3389
~~~
The `host` and `port` parameters are only used if a stand-alone (i.e., "not RDS-hosted") database has been targeted for hosting configuration data.
~~~
    # AWS account information so that Mothball can access the api
    AWS:
      region: us-west-1
    
      access_key: XXXXXXXXXXXXXXXXXXXX
    
      secret_key: YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
~~~
The above parameters define:
- The region that the RDS-hosted configuration database is located in.
- The AWS IAM user's access-key string
- The AWS IAM user's secret-key string
This selected IAM user must have sufficient rights to create an RDS instance and any associated security-group objects
~~~
    # For use with RDS (either existing or to create one)
    RDS:
      use_rds: True
      # Comma seperated for more than one security group.
      vpc_security_groups:
        - <Security_Group_ID>
    
      name: <RDS_Name>
~~~
The above parameters define:
- Whether an RDS-hosted database will be used
- A single security-group ID - or list of IDs - to associate to the RDS-hosted database
- The name of the RDS service to configure (this will be part of the RDS end-point name).

## Usage

```
python MbBackup.py --help
usage: MbBackup.py [-h] [--config FILENAME] [--terminate]

optional arguments:
  -h, --help         show this help message and exit
  --config FILENAME  This points to the mothball.config file to be used.
  --terminate        This option must be used in order to turn dryrun off. In
                     dryrun mode data is storedin the database; however will
                     not snapshot the volumes nor terminate the Instance.
                     Whenthis option is used it will turn off dryrun. Be
                     careful this will terminate all ec2instances in a region
                     for the account being used!

```



## Documentation
For information on installing and using Mothball, go to https://mothball.readthedocs.io.

Alternatively, you can install mkdocs with
 ```
 pip install mkdocs
 ```
 and then in the Mothball directory, run
 ```
 mkdocs serve
 ```
 This will start a light-weight server on `http://127.0.0.1:8000` containing the documentation on Mothball.
