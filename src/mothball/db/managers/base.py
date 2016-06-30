import abc
import time
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mothball.db.models.base import Base


class DBManager(object):
    """
    Interface for non-RDS databases.
    """

    def __init__(self, db_type, name, username, password, host, port):
        """

        :param db_type:
        :param name:
        :param username:
        :param password:
        :param host:
        :param port:
        """
        self.db_type = db_type
        self.name = name
        self.username = username
        self.password = password
        self.host = host
        self.port = port

    def create_db_session(self):
        """

        :return:
        :rtype: Database Session Object
        """
        dbsession = SQLConnect(self.host,
                               self.port,
                               dbname=self.dbname,
                               username=self.username,
                               password=self.password,
                               db_type=self.db_type
                               )

        return dbsession


class RDSManager(object):
    """
    Interface for RDS databases.
    """

    def __init__(self, db_type, name, dbname, username, password, awssession, vpc_sg):
        self.db_type = db_type
        self.name = name
        self.dbname = dbname
        self.username = username
        self.password = password
        self.Session = awssession
        self.vpc_sg = vpc_sg
        self.instance_info = None
        self.rds_session = None

    def _check_rds_instance_exists(self):
        return any(k for k in self.rds_session.describe_db_instances()['DBInstances']
                   if k['DBInstanceIdentifier'] == self.name.lower())

    def _get_rds_db_info(self):
        for instance in self.rds_session.describe_db_instances()['DBInstances']:
            if instance['DBInstanceIdentifier'] == self.name.lower():
                self.instance_info = instance

    def _create_rds_instance(self):

        if self.db_type.lower() != 'mysql':
            version = '9.5'
        else:
            version = '5.7'

        self.rds_session.create_db_instance(DBInstanceIdentifier=self.name,
                                            AllocatedStorage=200,
                                            DBInstanceClass='db.t2.micro',
                                            DBName=self.dbname,
                                            Engine=self.db_type,
                                            EngineVersion=version,
                                            MasterUsername=self.username,
                                            MasterUserPassword=self.password,
                                            VpcSecurityGroupIds=self.vpc_sg
                                            )

        self._get_rds_db_info()
        while 'Endpoint' not in self.instance_info:
            time.sleep(5)
            self._get_rds_db_info()

    def create_db_session(self):

        self.rds_session = self.Session.client('rds')

        if not self._check_rds_instance_exists():
            self._create_rds_instance()
        else:
            self._get_rds_db_info()

        dbsession = SQLConnect(self.instance_info['Endpoint']['Address'],
                               self.instance_info['Endpoint']['Port'],
                               dbname=self.dbname,
                               username=self.username,
                               password=self.password,
                               db_type=self.db_type
                               )

        return dbsession


class SQLConnect(object):
    """
    Interface for database connections.
    """

    def __init__(self, address, port, dbname='Backup', username='bull', password='bullbythehorns', db_type='managers'):
        self.dbname = dbname
        self.username = username
        self.password = password
        self.address = address
        self.port = port
        self.session = None
        self.db_type = db_type
        self.engine = None
        self.session = None

    # TODO breakout Mysql and Postgres to child classes that import SQLConenct (DBBase?)

    def _mysql(self):
        self.engine = create_engine('mysql+pymysql://{0}:{1}@{2}:{3}/{4}'.format(self.username,
                                                                                 self.password,
                                                                                 self.address,
                                                                                 self.port,
                                                                                 self.dbname))

    def _postgres(self):
        self.engine = create_engine('postgresql://{0}:{1}@{2}:{3}/{4}'.format(self.username,
                                                                              self.password,
                                                                              self.address,
                                                                              self.port,
                                                                              self.dbname))

    def _db_picker(self):
        if self.db_type == 'postgresql':
            self._postgres()
        else:
            self._mysql()

    def connect(self):

        if not self.engine:
            self._db_picker()

        Base.metadata.bind = self.engine
        dbsession = sessionmaker(bind=self.engine)
        self.session = dbsession()

    def create_tables(self):

        if not self.engine:
            self._db_picker()

        Base.metadata.create_all(self.engine)

    def close(self):
        self.session.close()

    def update(self, data_object):
        if not self.session:
            logging.warning('No db session has been made to create a record for.  self.connect first.')
        else:
            self.session.add(data_object)
            self.session.commit()