#!/usr/bin/env python3
import configparser
import boto3

import urllib3
from botocore.exceptions import ClientError
from pip._vendor import certifi

def main():
    config = configparser.ConfigParser()

    config.read('tunnelcheck.cfg')
    try:
        deviceidstr = config['waninfo']['deviceid']
        wantable = config['waninfo']['wantable']
        awsregion = config['waninfo']['awsregion']
    except KeyError as e:
        print("No config file, so pulling info from my user's AWS tags.")
        iam = boto3.resource("iam")
        user = iam.CurrentUser()
        tagset = user.tags
        for tag in tagset:
            if tag['Key'] == 'DeviceName':
                devicename = tag['Value']
            if tag['Key'] == 'DeviceID':
                deviceidstr = tag['Value']
            if tag['Key'] == 'AWSRegion':
                awsregion = tag['Value']
            if tag['Key'] == 'WANTable':
                wantable = tag['Value']

    deviceid = int(deviceidstr)


    dynamodb = boto3.resource("dynamodb", region_name=awsregion)
    table = dynamodb.Table(wantable)
    myip = ""
    try:
        response = table.get_item(Key={'DeviceID': deviceid})
    except ClientError as e:
        print(e.response['Error']['Message'])
        exit(1)
    else:
        item = response['Item']
    myip = item["WANIP"]
    http = urllib3.PoolManager(ca_certs=certifi.where())
    req = http.request('GET', 'https://ident.me/' )
    mywanip = req.data.decode('utf-8')
    if (myip==mywanip):
        print(f'My Public IP is {mywanip} and is correct in AWS')
    else:
        print(f'My IP should be {myip}, but it is {mywanip}')
    item["WANIP"] = mywanip
    if myip!=mywanip:
        print("Updating IP:")
        table.put_item(TableName=wantable, Item=item)
        print(item)

if __name__ == '__main__':
    main()

