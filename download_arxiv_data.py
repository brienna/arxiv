import boto3, tarfile, os, shutil, datetime

s3resource = None

def main():
    global s3resource
    global destination_bucket
    # Tell boto3 we want to use the resource from Amazon S3
    s3resource = boto3.resource("s3")
    # Initialize source bucket
    source_bucket = 'arxiv'

    # Collect all files for s3://arxiv/src/<file> 
    # Note: Limited to 1,000, need Paginator to get more?
    objects = s3resource.meta.client.list_objects(
        Bucket=source_bucket,
        RequestPayer='requester',
        Prefix='src/')

    # Copy file (only one for now)
    for file in objects["Contents"][:1]:
        key = file["Key"]
        if key.endswith('.tar'):
            # UNCOMMENT ONCE ALREADY GET THE FILE, OR DO CHECK FOR EXISTING
            # downloadFile(source_bucket, key) 
            #copyFileToS3(source_bucket, key)
            pass

    # unzip .tar file
    extractFile(key)


def copyFileToS3(source_bucket, key):
    destination_bucket = 'briennakh-arxiv'

    print("Copying s3://{}/{} to s3://{}/{}...".format(
        source_bucket,
        key,
        destination_bucket,
        key))

    # Copy file (source key) from source bucket 
    # to destination bucket, naming it destination key
    response_copy = s3resource.Object(
        destination_bucket,key).copy_from(
                CopySource='{}/{}'.format(source_bucket, key),
                RequestPayer='requester')

    # Check that it copied successfully
    if response_copy["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print("SUCCESS")


def downloadFile(source_bucket, key):
    # Ensure 'src' folder exists
    if not os.path.isdir('src'):
        os.makedirs('src')

    print("Downloading s3://{}/{} to {}...".format(
        source_bucket,
        key, 
        key))
    s3resource.meta.client.download_file(source_bucket, key, key, {'RequestPayer':'requester'})


def extractFile(filename):
    # Add date to error log
    log = open('error_log.txt', 'a')
    log.write('\n' + datetime.datetime.now().isoformat() + '\n')

    # Process if filename is a .tar file
    if not tarfile.is_tarfile(filename):
        print('can\'t unzip, not a .tar file')
        return
    print('Processing ' + filename + '...')
    tar = tarfile.open(filename)
    for subfile in tar.getmembers():
        # Open .tar subfile only if .gz
        if subfile.name.endswith('.gz'):
            try: 
                print('Processing ' + filename + '/' + subfile.name + '...')
                gz = tar.extractfile(subfile)
                gz = tarfile.open(fileobj=gz)
                # Extract file from .gz into 'latex' subfolder only if .tex
                for subsubfile in gz.getmembers():
                    if subsubfile.name.endswith('.tex'):
                        gz.extract(subsubfile, path='latex')
                print(subfile.name + ' extracted successfully')
            except tarfile.ReadError:
                # Append subfile name to error log
                print('error extracting ' + subfile.name + '...')
                log.write(subfile.name + '\n')
    tar.close()
    log.close()
    print(filename + ' processed successfully')


# If file is being run as a script on the command line
if __name__ == '__main__':
    main()



# NEXT STEPS:
# 1) Why are many .gz files throwing ReadErrors?
# 2) Do I need to actually extract the .tar and all the .gz?
# 3) Check each .tex file and only extract the ones that start with \document
# 4) In a different program, parse each .tex file for words (with latex module?)
# 5) Check if have existing .tar before downloading & writing over
# 6) Close any gz/tar files? 


