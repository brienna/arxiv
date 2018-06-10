# How to bulk access arXiv full-texts

Since its inception in 1991, arXiv, the main database for scientific preprints, has received almost [1.3 million submissions](https://arxiv.org/help/stats/2017_by_area/index). All of this data can be useful in analysis, so we may want to be able to access the full-texts in bulk. This post goes over how we can do this using Python 3 and the command line. 

## Amazon S3 info

Although the data is right there on the server, [it is not recommended to crawl arXiv directly](https://arxiv.org/help/robots) due to limited server capacity. However, arXiv has acknowledged the demand for bulk access by [making all full-texts available on Amazon S3](https://arxiv.org/help/bulk_data_s3), with monthly updates. 

arXiv stores their articles in the arxiv bucket. The requester has to pay. The data is in big tar files ordered by date (the last modification time of that file). This is kind of inconvenient, because we will need to process the entire arXiv corpus even if we are only interested in a specific category. 

Below we will go over the steps to download the full-texts, targeting the `astro-ph` category. 

### 1. Set up an AWS account. 

To be able to download anything from Amazon S3, you need an Amazon Web Services (AWS) account. Sign up [here](https://portal.aws.amazon.com/billing/signup). You'll have to register a credit card.

### 2. Create your configuration file. 

Create a file named `config.ini` and add your AWS configs:

```python
[DEFAULT]
ACCESS_KEY = access-key-value
SECRET_KEY = secret-key-value
```

To get your key values, follow the directions [here](https://www.cloudberrylab.com/blog/how-to-find-your-aws-access-key-id-and-secret-access-key-and-register-with-cloudberry-s3-explorer/) for root access keys. 

Do not make this file public. 

### 3. Create S3 resource & set configs.

Create a Python file that you'll run from the command line. In it, initialize a S3 resource, which is an object-oriented interface to the service, and configure it to use your root access.

```python
import boto3, configparser

s3resource = None

def setup():
    """Creates S3 resource & sets configs to enable download."""

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

if __name__ == '__main__':
    """Runs if script is called on command line"""

    # Create S3 resource & set configs
    setup()
```

### 4. Check `arxiv` bucket metadata.

arXiv maintains useful information about the data in their bucket in a file called `src/arXiv_src_manifest.xml`. Download this file to better understand what we're working with. 

```python
import boto3, configparser, os, botocore

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
            Key=key,  # name of key to download from
            Filename=key,  # path to file to download to
            ExtraArgs={'RequestPayer':'requester'})
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print('ERROR: ' + key + " does not exist in arxiv bucket")

if __name__ == '__main__':
    """Runs if script is called on command line"""

    # Download manifest file to current directory
    download_file('src/arXiv_src_manifest.xml')
```

*Note: The code will only show new or changed sections relevant to the current step, but the Python file contains code from all steps up to this one. The full file will be shown at the end.*

Explore the metadata. 

```python
from bs4 import BeautifulSoup

def explore_metadata():
    """Explores arxiv bucket metadata."""

    manifest = open('src/arXiv_src_manifest.xml', 'r')
    soup = BeautifulSoup(manifest, 'xml')

    # Print last time the manifest was edited
    timestamp = soup.arXivSRC.find('timestamp', recursive=False).string
    print("Manifest was last edited on " + timestamp)

    # Print number of files in bucket
    numOfFiles = len(soup.find_all('file'))
    print("arxiv bucket contains " + str(numOfFiles) + " .tar files")

if __name__ == '__main__':
    """Runs if script is called on command line"""

    # Explore the metadata in the manifest file
    explore_metadata()
```

When we run this code, we'll see when the manifest file was last updated, along with how many tar files the `arxiv` bucket holds. When I ran this code (on Sat., Jun. 9, 2018), the bucket contained 1,910 tars. 

### Download source files!

Remember that each TAR contains about 500MB of tar gzs, which contain the arXiv source files. While we must download all the TARs, we can extract these source files without the overhead of unzipping all the tars and tar gzs.