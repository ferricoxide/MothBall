#!/usr/bin/env python

import os
import yaml
import logging
import argparse

from mothball.managers.base import AWSManager

def get_config(filename):
    """
    Loads Yaml file into a dictionary for use in main.

    :param filename: Path to yaml file for parsing.
    :type filename: basestring

    :return: The data from the yaml config file.
    :rtype: dict
    """

    config = None
    if os.path.exists(filename):
        with open(filename) as f:
            data = f.read()
        config = yaml.load(data)
    else:
        logging.error('config file does not exist!')
    return config

def main(filename, dryrun):
    """
    This is the main caller for the mothball application. This file should be installed and executed on the
    command line.

    This function setups the cadence for backing up and terminating all available ec2 instances for an account.

    Cadence:
        First, it collects the data from the config file.
        Second, it creates an AWSManager which is the core of the mothball interface to aws.
        Third, it collects the account info for the EC2 instance it is being executed on.
        Fourth, it creates the Database connection for dumping data to. Finally it dumps the data to the Database.
        Finally, executes terminate across all instances returned from the get_info function.

    :param filename: This is the mothball.config file for executing the mothball application.
    :type filename: basestring
    :param dryrun: Holds the value for dryrun
    :type dryrun: bool

    :return: None
    """

    config = get_config(filename)
    aws = AWSManager(config['AWS']['region'],
                     config['AWS']['access_key'],
                     config['AWS']['secret_key'],
                     config['Database']['username'],
                     config['Database']['password'],
                     config['Database']['name'],
                     config['Database']['host'],
                     config['Database']['port'],
                     config['Database']['type'],
                     dryrun,
                     config['RDS']['use_rds'],
                     config['RDS']['name'],
                     *config['RDS']['vpc_security_groups'])

    aws.get_account_info()
    aws.get_db_connection()

    instances = aws.backup_instances()

    aws.terminate(instances)




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='filename', default='mothball.config',
                        help='This points to the mothball.config file to be used.')
    parser.add_argument('--terminate', dest='dryrun', default=True, action='store_false',
                        help='This option must be used in order to turn dryrun off.  In dryrun mode data is stored'
                             'in the database; however will not snapshot the volumes nor terminate the Instance.  When'
                             'this option is used it will turn off dryrun. Be careful this will terminate all ec2'
                             'instances in a region for the account being used!')

    args = parser.parse_args()

    main(args.filename, args.dryrun)
