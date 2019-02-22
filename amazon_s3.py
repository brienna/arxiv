import configparser, boto3


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


	def __init__(self):
		self.setup()
		


