#!/bin/python
#
# Iterate all the instances within a specific region and identify
# all attached EIP objects. Record EIP information into the 'EIP'
# (MySQL) database table.
#
#################################################################
import argparse
import boto3
import json
import subprocess
from MothDBconnect import DbConnect, DbCnctInfo


###################################################################
# Get list of regions in service
#    Need this for bounds-checking, but it's a Chicken/Egg problem:
#    need AWS CLI config with default-region set
def ValidRegion():
    regraw = subprocess.Popen(
            "aws ec2 describe-regions --query 'Regions[].RegionName[]' --out text",
            shell=True,
            stdout=subprocess.PIPE).stdout.read()

    return regraw.split( )


######################################
# Get list of SecurityGroups in region
def GetSGs(args):
    ec2 = session.client(
        'ec2',
        region_name = args.region,
        aws_access_key_id = args.key,
        aws_secret_access_key = args.secret
    )

    sgStructMain = ec2.describe_security_groups()['SecurityGroups']
    sgCount = len(sgStructMain)

    # Iterate security-groups, extracting data
    for perSgStruct in sgStructMain:
        accountId = perSgStruct['OwnerId']
        sgId =  perSgStruct['GroupId']
        sgName =  perSgStruct['GroupName']
        sgVpsAssoc = perSgStruct['VpcId']
        sgIngresPerms = perSgStruct['IpPermissions']
        sgEgresPerms = perSgStruct['IpPermissionsEgress']

        # Send off to MySQL-insert function
        SgInfoMysql(accountId, sgId, sgName, sgVpsAssoc, sgIngresPerms, sgEgresPerms)


########################################
# Push SecurityGroup info to MySQL table
def SgInfoMysql(accountId, sgId, sgName, sgVpsAssoc, sgIngresPerms, sgEgresPerms):

    insert_string = (
        "INSERT INTO SecurityGroup "
	"("
	  "AccountId, "
	  "sgId, "
	  "sgName, "
	  "vpcAssn, "
	  "ingressRules, "
	  "egressRules"
	") "
	"Values ("
	  "%(AccountId)s, "
	  "%(sgId)s, "
	  "%(sgName)s, "
	  "%(vpcAssn)s, "
	  "%(ingressRules)s, "
	  "%(egressRules)s"
	"); "
    )

    insert_data = {
        'AccountId'	: accountId,
	'sgId'		: sgId,
	'sgName'	: sgName,
	'vpcAssn'	: sgVpsAssoc,
	'ingressRules'	: json.dumps(sgIngresPerms),
	'egressRules'	: json.dumps(sgEgresPerms)
    }

    cursor.execute(insert_string, insert_data)
    dbconn.commit()


############################
# Commandline option-handler
parseit = argparse.ArgumentParser()

parseit.add_argument("-r", "--region",
                     choices = ValidRegion(),
                     help="AWS Region",
                     required=True)
parseit.add_argument("-k", "--key",
                     help="AWS access-key ID")
parseit.add_argument("-s", "--secret",
                     help="AWS access-key secret")
parseit.add_argument("-t", "--target-account",
                     help="AWS account to manage",
                     required=True)

# Assign CLI argument-values to fetchable name-space
args = parseit.parse_args()

AWSaccount = args.target_account

# Initialize session/connection to AWS
session = boto3.Session(
    region_name = args.region,
    aws_access_key_id = args.key,
    aws_secret_access_key = args.secret
)

# Initialize connection to MySQL
dbconn = DbConnect(DbCnctInfo('testclt'))
cursor = dbconn.cursor()

GetSGs(args)

# Clean up connection to MySQL
cursor.close()
dbconn.close()
