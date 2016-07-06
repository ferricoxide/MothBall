import abc
import logging

from mothball.db.models.base import EBS, EIP, SecurityGroup, Instances


class AWSConfigurationManager(object):
    """
    Abstract Base Class for AWS Services Classes.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, ec2_session, db_session):
        """
        :param ec2_session: ec2 session to collect data from.
        :type ec2_session: ec2 session object
        :param db_session: database session to backup data to.
        :type db_session: database session object
        """
        self.ec2_session = ec2_session
        self.db_session = db_session

    @abc.abstractmethod
    def create_record(self, account_id, instance_id):
        """
        Abstract method for creating a record for the AWS Service.

        :param account_id: The account id being backed up.
        :type account_id: basestring
        :param instance_id: The instance id being backed up.
        :type instance_id: basestring
        """
        return


class EBSManager(AWSConfigurationManager):
    """
    Class for backing up the Elastic Book Store configuration information for a particular instance.
    """

    def __init__(self, ec2_session, db_session):
        super(EBSManager, self).__init__(ec2_session, db_session)

    def _volume_snapshot(self, volume_id):
        """
        Private method for creating a volume snapshot for archival.

        :param volume_id: The volume id being snapshotted.
        :type volume_id: basestring
        """

        logging.info('Snapshot of Volume: {0}'.format(volume_id))
        # TODO Try Except
        self.ec2_session.create_snapshot(VolumeId=volume_id,
                                         Description='Snapshot before MothBall Deregister for {0}'.format(volume_id)
                                         )

    def create_record(self, account_id, instance_id, dry_run=True):

        devices = self.ec2_session.Instance(instance_id).block_device_mappings

        for dev in devices:
            if not self.db_session.session.query(EBS).filter_by(volumeId=dev['Ebs']['VolumeId']).all():

                new_ebs = EBS()
                new_ebs.AccountId = account_id
                new_ebs.instanceId = instance_id
                new_ebs.attachmentSet = dev['DeviceName']

                volume = self.ec2_session.Volume(dev['Ebs']['VolumeId'])
                new_ebs.volumeId = volume.volume_id
                new_ebs.size = volume.size
                new_ebs.volumeType = volume.volume_type
                new_ebs.iops = volume.iops
                new_ebs.availabilityZone = volume.availability_zone
                new_ebs.tagSet = volume.tags
                if hasattr(new_ebs.tagSet, '__dict__'):
                    new_ebs.tagSet = new_ebs.tagSet.__dict__
                new_ebs.createTime = volume.create_time
                new_ebs.encrypted = volume.encrypted
                new_ebs.kmsKeyId = volume.kms_key_id
                new_ebs.snapshotId = volume.snapshot_id
                new_ebs.status = volume.state
                self.db_session.update(new_ebs)

                if not dry_run:
                    self._volume_snapshot(volume.volume_id)
            else:
                logging.debug('VolumeId {0} has already been backed up.'.format(dev['Ebs']['VolumeId']))


class EIPManager(AWSConfigurationManager):
    """
    Class for backing up the Elastic IP configuration information for a particular instance.
    """

    def __init__(self, ec2_session, db_session):
        super(EIPManager, self).__init__(ec2_session, db_session)

    def create_record(self, account_id, instance_id):

        interfaces = self.ec2_session.Instance(instance_id).network_interfaces_attribute

        for interface in interfaces:
            if not self.db_session.session.query(EIP).filter_by(interfaceId=interface['NetworkInterfaceId']).all():
                new_eip = EIP()
                new_eip.AccountId = account_id
                new_eip.instanceId = instance_id

                nid = self.ec2_session.NetworkInterface(interface['NetworkInterfaceId'])
                # new_eip.association = nid.association
                # new_eip.assocAttr = nid.association_attribute
                new_eip.attachment = nid.attachment
                if new_eip.attachment and isinstance(new_eip.attachment, dict) and 'AttachTime' in new_eip.attachment:
                    new_eip.attachment['AttachTime'] = new_eip.attachment['AttachTime'].isoformat()
                new_eip.description = nid.description
                new_eip.groups = nid.groups
                new_eip.interfaceId = nid.id
                new_eip.type = nid.interface_type
                new_eip.MACaddress = nid.mac_address
                new_eip.owner = nid.owner_id
                new_eip.privateIP = nid.private_ip_address
                new_eip.privateIPs = nid.private_ip_addresses
                new_eip.requester = nid.requester_id
                new_eip.managed = nid.requester_managed
                new_eip.SrcDstChk = nid.source_dest_check
                new_eip.status = nid.status
                new_eip.subnetId = nid.subnet_id
                new_eip.tagSet = nid.tag_set
                new_eip.vpcId = nid.vpc_id

                self.db_session.update(new_eip)
            else:
                logging.debug('Interface ID {0} has already been backed up.'.format(interface['NetworkInterfaceId']))

class SecurityGroupManager(AWSConfigurationManager):
    """
    Class for backing up the Security Group configuration information for a particular instance.
    """

    def __init__(self, ec2_session, db_session):
        super(SecurityGroupManager, self).__init__(ec2_session, db_session)

    def create_record(self, account_id, instance_id):

        sgs = self.ec2_session.Instance(instance_id).security_groups

        for sg in sgs:
            if not self.db_session.session.query(SecurityGroup).filter_by(sgId=sg['GroupId']).all():
                new_sg = SecurityGroup()

                secgroup = self.ec2_session.SecurityGroup(sg['GroupId'])
                new_sg.sgId = sg['GroupId']
                new_sg.AccountId = account_id
                new_sg.instanceId = instance_id
                new_sg.description = secgroup.description
                new_sg.name = secgroup.group_name
                new_sg.ingressRules = secgroup.ip_permissions
                new_sg.egressRules = secgroup.ip_permissions_egress
                new_sg.vpcId = secgroup.vpc_id
                new_sg.tagSet = secgroup.tags

                self.db_session.update(new_sg)
            else:
                logging.debug('Security group {0} has already been backed up.'.format(sg['GroupId']))


class InstanceManager(AWSConfigurationManager):
    """
    Class for backing up the Instance configuration information for a particular instance.
    """

    def __init__(self, ec2_session, db_session):
        super(InstanceManager, self).__init__(ec2_session, db_session)

    def create_record(self, account_id, instance_id):

        new_inst = Instances()

        if not self.db_session.session.query(Instances).filter_by(instanceId=instance_id).all():
            new_inst.AccountId = account_id
            new_inst.instanceId = instance_id

            # TODO This needs to be corrected to the proper map.
            new_inst.AvailabilityZone = ''

            self.db_session.update(new_inst)
        else:
            logging.debug('Instance {0} has already been backed up.'.format(instance_id))
