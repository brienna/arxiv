import boto3, tarfile, os, shutil, datetime, sys
from bs4 import BeautifulSoup
from bs4 import NavigableString

s3resource = None

def setup():
    """Sets up data download."""

    # Tell boto3 we want to use the resource from Amazon S3
    global s3resource
    s3resource = boto3.resource("s3")
    # Set source bucket name
    source_bucket = 'arxiv'

    # Fetch file list for s3://arxiv/src directory
    # Note: Limited to 1,000, need Paginator to get more?
    objects = s3resource.meta.client.list_objects(
        Bucket=source_bucket,
        RequestPayer='requester',
        Prefix='src/')

    # Download and extract .tar files that haven't been downloaded & extracted yet
    # Note: Only downloading one for now
    for file in objects["Contents"][:1]:
        key = file["Key"]
        if key.endswith('.tar'):
            if os.path.exists(key):
                print(key + ' already has been downloaded and extracted.')
            else:
                downloadFile(source_bucket, key)
                extractFile(key)

    parseFiles()
    
    # copyFileToS3(source_bucket, key)


def copyFileToS3(source_bucket, key):
    """
    Copies file from source bucket to specified S3 bucket.

    Parameters
    ----------
    source_bucket : str
        Name of source bucket
    key : str
        Name of file to copy
    """

    # Set destination bucket name for file to be copied to
    destination_bucket = 'briennakh-arxiv'
    print("Copying s3://{}/{} to s3://{}/{}...".format(
        source_bucket,
        key,
        destination_bucket,
        key))

    # Copy file from source bucket to destination bucket
    response_copy = s3resource.Object(
        destination_bucket,key).copy_from(
                CopySource='{}/{}'.format(source_bucket, key),
                RequestPayer='requester')

    # Check that file copied successfully
    if response_copy["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print("SUCCESS COPYING " + key + " to " + destination_bucket)


def downloadFile(source_bucket, key):
    """
    Downloads file from source bucket to computer.

    Parameters
    ----------
    source_bucket : str
        Name of source bucket
    key : str
        Name of file to download
    """

    # Ensure 'src' folder exists
    if not os.path.isdir('src'):
        os.makedirs('src')

    # Download file
    print("Downloading s3://{}/{} to {}...".format(
        source_bucket,
        key, 
        key))
    s3resource.meta.client.download_file(
        source_bucket, 
        key, 
        key, 
        {'RequestPayer':'requester'})


def extractFile(filename):
    """
    Extracts specified file.

    Parameters
    ----------
    filename : str
        Name of file to extract
    """

    total_successful = 0
    total = 0

    # Start new section in error log
    log = open('error_log.txt', 'a')
    log.write('\n' + datetime.datetime.now().isoformat() + '\n')

    # Proceed with file extraction if .tar
    if not tarfile.is_tarfile(filename):
        print('can\'t unzip ' + filename + ', not a .tar file')
        return
    print('Processing ' + filename + '...')
    tar = tarfile.open(filename)
    for subfile in tar.getmembers():
        # Open .tar subfile only if .gz and begins with 'astro-ph'
        if subfile.name.endswith('.gz') and 'astro-ph' in subfile.name:
            total = total + 1
            print('opening ' + subfile.name)
            try: 
                print('Processing ' + filename + '/' + subfile.name + '...')
                gz = tar.extractfile(subfile)
                gz = tarfile.open(fileobj=gz)
                # Extract file from .gz into 'latex' subfolder only if .tex
                for subsubfile in gz.getmembers():
                    if subsubfile.name.endswith('.tex'):
                        gz.extract(subsubfile, path='latex')
                print(subfile.name + ' extracted successfully')
                total_successful = total_successful + 1
            except tarfile.ReadError:
                # If error extracting subfile, note in error log
                print('error extracting ' + subfile.name + '...')
                log.write(subfile.name + '\n')
    tar.close()
    log.close()

    print(filename + ' extraction complete.')
    print('Extraction results for ' + filename + '...')
    print('Total number of astro-ph .gz files: ' + str(total))
    print('Total number of astro-ph .gz files successfully extracted: ' + str(total_successful))


def parseFiles():
    """
    Parses downloaded document .tex files for word content.
    We are only interested in the article body, defined by /section tags.
    """

    for file in os.listdir("xml"):
        if file.endswith('.xml'):
            print('\nChecking ' + file + '...')
            with open("xml/" + file) as f:
                soup = BeautifulSoup(f, "xml")
                getText(soup)


def getText(soup):
    """
    Extracts text from given "section" node and any nested "subsection" nodes. 

    Parameters
    ----------
    node : list
        A "section" node in a .tex document 
    """

    corpus = open('corpus.txt', 'a')

    # Process sections
    sections = soup.find_all('section')
    for section in sections:
        print(section.name)
        # Process citations
        citations = section.find_all('cite')
        for citation in citations:
            # Render inline citations
            if citation['class'] == 'ltx_citemacro_citet':
                # Get ref #
                citet = citation.bibref['bibrefs']
                # Using ref #, find inline citation in bibliography
                citetStr = soup.find('bibitem', attrs={'key': citet}).find('bibtag', attrs={'role': 'refnum'}).string
                # Replace citation tag with in-text citation str
                citation.replace_with(NavigableString(citetStr))
            # Otherwise remove citation
            else: 
                citation.decompose()
        # Remove footnotes
        footnotes = section.find_all('note')
        for footnote in footnotes:
            footnote.decompose()
        # Append document to corpus
        corpus.write(section.get_text())


if __name__ == '__main__':
    """Runs if script called on command line"""
    setup()



