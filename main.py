from metadata import Metadata
from gdrive import Gdrive
from amazon_s3 import Amazon_S3
import utils
import os
import multiprocessing as mp
import shutil

global g
global gdrive_tarfiles
global s3
global m


def work(key):
	'''
	Defines the work to be done in each multiprocessing worker.
	'''
	
	global g
	global s3
	global m

	print('{} is working on {}...'.format(mp.current_process(), key))
	downloaded_filename = ''.join(['latex/', os.path.splitext(os.path.basename(key))[0]])
	gtar = None
	for gfile in gdrive_tarfiles:
		if gfile.metadata['title'] == os.path.basename(key):
			gtar = gfile
	
	#if tarfile is on local storage, extract it from here
	try:
		if os.path.isfile(key):
			utils.extract(key, m.identifiers)
			if len(os.listdir(downloaded_filename)) > 0:
				utils.convert(downloaded_filename)
			else:
				print('Tarfile contains no astro-ph submissions.')
			os.remove(key)
			shutil.rmtree(downloaded_filename, ignore_errors=True)
			print('Completed and removed {}'.format(key))
		# If tarfile is in Google Drive, extract it from there
		elif gtar:
			g.download(gtar, key)
			utils.extract(key, m.identifiers)
			if len(os.listdir(downloaded_filename)) > 0:
				utils.convert(downloaded_filename)
			else:
				print('Tarfile contains no astro-ph submissions.')
			os.remove(key)
			shutil.rmtree(downloaded_filename, ignore_errors=True)
			print('Completed and removed {}'.format(key))
		# Otherwise, extract it from S3
		else:
			s3.download_file(key)
			utils.extract(key, m.identifiers)
			if len(os.listdir(downloaded_filename)) > 0:
				utils.convert(downloaded_filename)
			else:
				print('Tarfile contains no astro-ph submissions.')
			g.upload(key)
			os.remove(key)
			shutil.rmtree(downloaded_filename, ignore_errors=True)
			print('Completed and removed {}'.format(key))
	except KeyboardInterrupt:
		# If interrupted, remove the downloaded filename, so that any incomplete downloads aren't recognized as complete
		print('INTERRUPTED: ' + downloaded_filename)
		if os.path.isdir(downloaded_filename):
			print('Removing ' + downloaded_filename)
			shutil.rmtree(downloaded_filename, ignore_errors=True)
		if os.path.isdir('temp'):
			print('Removing ./temp')
			shutil.rmtree('temp', ignore_errors=True)
		if os.path.isfile(downloaded_filename + '.txt'):
			print('Removing ' + downloaded_filename + '.txt')
			os.remove(downloaded_filename + '.txt')
		raise
	except Exception:
		if os.path.isdir(downloaded_filename):
			print('Removing ' + downloaded_filename)
			shutil.rmtree(downloaded_filename, ignore_errors=True)
		if os.path.isdir('temp'):
			print('Removing ./temp')
			shutil.rmtree('temp', ignore_errors=True)
		if os.path.isfile(downloaded_filename + '.txt'):
			print('Removing ' + downloaded_filename + '.txt')
			os.remove(downloaded_filename + '.txt')
		raise


def main():
	# Get identifiers for astro-ph preprints
	global m
	m = Metadata(update=True)
	print('Identifiers collected: {}'.format(len(m.identifiers)))

	# Connect to Google Drive
	global g
	global gdrive_tarfiles
	g = Gdrive() 
	gdrive_tarfiles = g.get_tarfiles()
	print('Tarfiles on Google Drive: {}'.format(len(gdrive_tarfiles)))

	# Connect to Amazon S3 and get page iterator
	global s3
	s3 = Amazon_S3()

	# Set up the parallel task pool to use all available processors
	pool = mp.Pool(processes=mp.cpu_count())

	# Iterate through each page
	for page in s3.get_page_iterator():
		# Collect all tars on that page if they haven't already been downloaded 
		tasks = [file['Key'] for file in page['Contents'] if file['Key'].endswith('.tar') and not os.path.isdir(''.join(['latex/', os.path.splitext(os.path.basename(file['Key']))[0]]))]
		
		# Run the jobs
		try:
			pool.map(work, tasks)
			pool.join()
		except KeyboardInterrupt:
			print('\nYou interrupted the script!')
			pool.terminate()
		except Exception as e:
			print('\nSomething went wrong: {}'.format(e))
			pool.terminate()


if __name__ == "__main__":
	main()

