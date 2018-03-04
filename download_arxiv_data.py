import boto3, tarfile, os, shutil

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
            #downloadFile(source_bucket, key)
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
    if not tarfile.is_tarfile(filename):
        print('can\'t unzip, not a .tar file')
        return

    # Proceed if filename is a .tar file
    print('Unzipping ' + filename + '...')
    tar = tarfile.open(filename)
    for item in tar:
        # Extract from .tar into 'temp' subfolder only if .gz
        if item.name.endswith('.gz'):
            item.name = os.path.basename(item.name) # reset path to remove parent directories like '0001'
            # Ensure 'temp' folder exists
            if not os.path.isdir('temp'):
                os.makedirs('temp')
            tar.extract(item, path='temp')
            # Extract from .gz into 'temp' subfolder only if .tex
            try: 
                print('Unzipping ' + item.name + '...')
                gz = tarfile.open('temp/' + item.name, mode='r:gz')
                # Only extract .tex files
                for file in gz:
                    if file.name.endswith('.tex'):
                        # Then read into the file and see if it starts with \document
                        gz.extract(file, path='latex')
                print(item.name + ' extracted successfully')
            except tarfile.ReadError:
                # Move to 'error' folder, ensuring it exists
                if not os.path.isdir('error'):
                    os.makedirs('error')
                os.rename('temp/' + item.name, 'error/' + item.name)
                print('error extracting ' + item.name + '...')
            gz.close()
    tar.close()
    print(filename + ' extracted successfully')
    shutil.rmtree('temp')


# If file is being run as a script on the command line
if __name__ == '__main__':
    main()
