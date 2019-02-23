import configparser, boto3, botocore


class Amazon_S3(object):
	s3resource = None

	def setup(self):
		'''
		Creates S3 resource & sets configs to enable download.
		'''

		# Securely import configs from private AWS config file
		configs = configparser.ConfigParser()
		configs.read('config.ini')

		# Create S3 resource & set configs
		self.s3resource = boto3.resource(
			's3',  # the AWS resource we want to use
			aws_access_key_id=configs['DEFAULT']['ACCESS_KEY'],
			aws_secret_access_key=configs['DEFAULT']['SECRET_KEY'],
			region_name='us-east-1'  # same region the arxiv bucket is in
		)


	def get_page_iterator(self):
		'''
		Gets page iterator from arxiv bucket. 
		'''

		paginator = self.s3resource.meta.client.get_paginator('list_objects_v2')
		page_iterator = paginator.paginate(
			Bucket='arxiv',
			RequestPayer='requester',
			Prefix='src/'
		)

		return page_iterator

	def download_file(self, key):
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
	    
	    print('Downloading s3://arxiv/{}'.format(key))
	    
	    # Download file
	    try:
	        self.s3resource.meta.client.download_file(
	            Bucket='arxiv', 
	            Key=key,  # name of key to download from
	            Filename=key,  # path to file to download to
	            ExtraArgs={'RequestPayer':'requester'})
	    except botocore.exceptions.ClientError as e:
	        if e.response['Error']['Code'] == "404":
	            print('ERROR: ' + key + " does not exist in arxiv bucket")
	            
	    print('Successfully downloaded s3://arxiv/{} to {}'.format(key, key))


	def __init__(self):
		self.setup()
		


