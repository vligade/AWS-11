import boto3
import yaml
import argparse
import subprocess
import sys
import xlwt
import csv
import os
import glob


envList = ['default', 'd', 'q', 'e', 'l', 'p']

parser = argparse.ArgumentParser(description='Checking ami')
parser.add_argument('-b', '--boxName', type=str)
parser.add_argument('-a', '--amazonCorrectPAmiName', type=str)
parser.add_argument('-c', '--centOSCorrectPAmiName', type=str)
parser.add_argument('-r', '--rhelCorrectPAmiName', type=str)
arguments = parser.parse_args()
filePath = 'eib/manifest/services/' + arguments.boxName
yamlList = subprocess.check_output(['find', filePath, '-name', '*.yml'])

#print arguments.boxName


# Removes the last element of the fixed fil
def fix_file_array(yamlArray):
    fileArray = []
    for line in yamlArray.split('\n'):
        fileArray.append(line)
    return fileArray[:-1]

# Function to check whether AWS ami exists and writes into CSV files
def write_parent_into_csv(env, file, ami, aminame):
    for attr in ami.values()[0]:
        for tag in attr['Tags']:
            #print tag
            with open('AmiError-' + arguments.boxName + '.csv', 'a') as fp:
                csvwriter = csv.writer(fp, delimiter=',')
                #print file
                if tag['Key'] == "ParentAmiName":
                    if "amazon" in tag['Value'] and tag['Value'] != arguments.amazonCorrectPAmiName:
                        data = [env, file, aminame, tag['Value']]
                        #print env, file, aminame, tag['Value']
                        csvwriter.writerow(data)
                    elif "centos" in tag['Value'] and tag['Value'] != arguments.centOSCorrectPAmiName:
                        data = [env, file, aminame, tag['Value']]
                        csvwriter.writerow(data)
                    elif "rhel" in tag['Value'] and tag['Value'] != arguments.rhelCorrectPAmiName:
                        data = [env, file, aminame, tag['Value']]
                        csvwriter.writerow(data)
                    with open('FullReport-' + arguments.boxName + '.csv', 'a') as rp:
                        csvwriter = csv.writer(rp, delimiter=',')
                        data = [env, file, aminame, tag['Value']]
                        #print env, file, aminame, tag['Value']
                        csvwriter.writerow(data)
        if "ParentAmiName" not in [x['Key'] for x in attr.values()[2]]:
            #print aminame
            with open('FullReport-' + arguments.boxName + '.csv', 'a') as rp:
                csvwriter = csv.writer(rp, delimiter=',')
                data = [env, file, aminame, "N/A - No Tag"]
                csvwriter.writerow(data)
            with open('AmiError-' + arguments.boxName + '.csv', 'a') as fp:
                csvwriter = csv.writer(fp, delimiter=',')
                data = [env, file, aminame, "N/A - No Tag"]
                csvwriter.writerow(data)

# Writes into csv file
def check_ami_exists(env, file, ami):
    with open('AmiError-' + arguments.boxName + '.csv', 'a') as fp:
        csvwriter = csv.writer(fp, delimiter=',')
        if not ami.values()[0]:
            data = [env, file, "N/A", "N/A"]
            csvwriter.writerow(data)
    with open('FullReport-' + arguments.boxName + '.csv', 'a') as rp:
        csvwriter = csv.writer(rp, delimiter=',')
        if not ami.values()[0]:
            data = [env, file, "N/A", "N/A"]
            csvwriter.writerow(data)


def main():

    fileArray = fix_file_array(yamlList)

# Creates header within AmiError
    with open('AmiError-' + arguments.boxName + '.csv', 'w') as fp:
        csvwriter = csv.writer(fp, delimiter=',')
        dataH = ["ENV", "YAML FILE", "YAML AMI", "PARENT AMI NAME"]
        csvwriter.writerow(dataH)

    # Creates header within FullReport
    with open('FullReport-' + arguments.boxName + '.csv', 'w') as rp:
        csvwriter = csv.writer(rp, delimiter=',')
        dataA = ["ENV", "YAML FILE", "YAML AMI", "PARENT AMI NAME"]
        csvwriter.writerow(dataA)

    try:
        client = boto3.client('ec2', region_name='us-west-2')
    except Exception as e:
        print Exception
        sys.exit(1)

    for file in fileArray:
        fileObj = yaml.load(open(file))
        for env in envList:
            if ("cfn-params" in fileObj) and env in fileObj['cfn-params'] and (fileObj['cfn-params'][env] is not None) \
                    and ("ami-name" in fileObj['cfn-params'][env]):
                aminame = fileObj['cfn-params'][env]['ami-name']
                ami = client.describe_images(Filters=[{'Name': 'name', 'Values': [aminame]}])
                check_ami_exists(env, file, ami)
                write_parent_into_csv(env, file, ami, aminame)

    # Merges both files into a single workbook and saves as AmiReport
    wb = xlwt.Workbook()
    for filename in glob.glob("*.csv"):
        (f_path, f_name) = os.path.split(filename)
        (f_short_name, f_extension) = os.path.splitext(f_name)
        ws = wb.add_sheet(f_short_name)
        Reader = csv.reader(open(filename, 'rb'))
        for rowx, row in enumerate(Reader):
            for colx, value in enumerate(row):
                ws.write(rowx, colx, value)
    wb.save(arguments.boxName + "-AmiReport.xls")

    # Deletes the extra CSV files
    os.remove('AmiError-' + arguments.boxName + '.csv')
    os.remove('FullReport-' + arguments.boxName + '.csv')


if __name__ == "__main__":
    main()



