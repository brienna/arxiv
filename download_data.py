import boto3, configparser
import boto3, configparser, os, botocore
from bs4 import BeautifulSoup
import json
from datetime import datetime

s3resource = None

def setup():
    """Creates S3 resource & sets configs to enable download."""

    print('Connecting to Amazon S3...')

    # Securely import configs from private config file
    configs = configparser.SafeConfigParser()
    configs.read('config.ini')

    # Create S3 resource & set configs
    global s3resource
    s3resource = boto3.resource(
        's3',  # the AWS resource we want to use
        aws_access_key_id=configs['DEFAULT']['ACCESS_KEY'],
        aws_secret_access_key=configs['DEFAULT']['SECRET_KEY'],
        region_name='us-east-1'  # same region arxiv bucket is in
    )

def download_file(key):
    """
    Downloads given filename from source bucket to destination directory.

    Parameters
    ----------
    key : str
        Name of file to download
    """

    # Ensure src directory exists 
    if not os.path.isdir('src'):
        os.makedirs('src')

    # Download file
    print('\nDownloading s3://arxiv/{} to {}...'.format(key, key))

    try:
        s3resource.meta.client.download_file(
            Bucket='arxiv', 
            Key=key,  # name of file to download from
            Filename=key,  # path to file to download to
            ExtraArgs={'RequestPayer':'requester'})
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print('ERROR: ' + key + " does not exist in arxiv bucket")

def explore_metadata():
    """Explores arxiv bucket metadata."""

    print('\narxiv bucket metadata:')

    with open('src/arXiv_src_manifest.xml', 'r') as manifest:
        soup = BeautifulSoup(manifest, 'xml')

        # Print last time the manifest was edited
        timestamp = soup.arXivSRC.find('timestamp', recursive=False).string
        print('Manifest was last edited on ' + timestamp)

        # Print number of files in bucket
        numOfFiles = len(soup.find_all('file'))
        print('arxiv bucket contains ' + str(numOfFiles) + ' tars')

        # Print total size
        total_size = 0
        for size in soup.find_all('size'):
            total_size = total_size + int(size.string)
        print('Total size: ' + str(total_size/1000000000) + ' GB')

    print('')

def begin_download():
    """Sets up download of tars from arxiv bucket."""

    print('Beginning tar download & extraction...')

    # Create a reusable Paginator
    paginator = s3resource.meta.client.get_paginator('list_objects_v2')

    # Create a PageIterator from the Paginator
    page_iterator = paginator.paginate(
        Bucket='arxiv',
        RequestPayer='requester',
        Prefix='src/'
    )

    # Download and extract tars
    numFiles = 0
    for page in page_iterator:
        numFiles = numFiles + len(page['Contents'])
        for file in page['Contents']:
            key = file['Key']
            # If current file is a tar
            if key.endswith('.tar'):
                download_file(key)
            
    print('Processed ' + str(numFiles - 1) + ' tars')  # -1 

if __name__ == '__main__':
    """Runs if script is called on command line"""

    # Create S3 resource & set configs
    setup()

    # Download manifest file to current directory
    download_file('src/arXiv_src_manifest.xml')

    # Explore bucket metadata 
    explore_metadata()

    # Begin tar download & extraction 
    begin_download()
    