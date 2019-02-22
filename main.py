from metadata import Metadata
from gdrive import Gdrive
from amazon_s3 import Amazon_S3
import tarfile, gzip, shutil, os, glob, re, pathlib
import subprocess as sp, multiprocessing as mp


def extract(filepath, identifiers):
	'''
	Extracts astro-ph submissions from given tar filepath.
	'''
	
	# Quit file extraction if given file is not tarfile
	if not tarfile.is_tarfile(filepath):
		print('can\'t unzip {}, not a .tar file'.format(filepath))
	
	total_tex = 0
	tar_dir = 'latex/' + os.path.splitext(os.path.basename(filepath))[0] + '/'

	# Create .tar directory if it doesn't exist
	if not os.path.isdir(tar_dir):
		os.makedirs(tar_dir)
		
	# Open tarfile, read-only
	print('Opening {}'.format(filepath))
	tar = tarfile.open(filepath)
	# Iterate over submissions, extracting only those that belong to the astro-ph category
	for submission in tar.getmembers():
		# Create submission directory if it doesn't exist
		submission_id = os.path.splitext(os.path.basename(submission.name))[0]
		submission_path = tar_dir + '/' + submission_id
		if submission.name.endswith('.gz') and identifiers.str.contains(submission_id).any():
			if not os.path.isdir(submission_path):
				os.makedirs(submission_path)
			#### Extract here.........
			try:
				gz_obj = tar.extractfile(submission) 
				gz = tarfile.open(fileobj=gz_obj) 
				gz.extractall(path=submission_path)
				total_tex += 1
			except tarfile.ReadError:
				# Extract the entire .gz because we cannot read it using tarfile 
				# Note that these .gzs are single .tex files with no extension specified
				tar.extract(submission, path='temp')
				# Uncompress the .gz file using gzip instead and place it with the other .tex files
				with gzip.open('temp/' + submission.name, 'rb') as f_in:
					basename = os.path.splitext(os.path.basename(submission.name))[0]
					with open(tar_dir + submission_id + '/' + basename + '.tex', 'wb+') as f_out:
						shutil.copyfileobj(f_in, f_out)
						total_tex += 1
	tar.close()
	
	print(filepath + ' extraction complete')
	print('Number of .tex files obtained: ' + str(total_tex) + '\n')


def get_all_preprints_from_tarfile(base_path):
	'''Collects filepaths for all preprints within
	given folder. Returns an array of strings, each
	string representing the path of a preprint.
	'''
	
	# Initialize variables
	empty_submissions = []
	preprints = []
	corrupt_submissions = []
	submission_count = 0
	texfile_count = 0
	
	# Walk through each submission directory
	submission_dirs = os.listdir(base_path)
	submission_count += len(submission_dirs)
	for submission in submission_dirs:
		
		# If current path isn't a directory, skip
		submission_path = base_path + '/' + submission
		if not os.path.isdir(submission_path):
			submission_count -= 1
			continue

		arxiv_id = os.path.basename(submission_path) # used to note empty or corrupt submissions 

		# If submission is empty, note & skip
		texs = glob.glob(submission_path + '/**/*.tex', recursive=True)
		texfile_count += len(texs)
		if len(texs) == 0:
			empty_submissions.append(arxiv_id)
			continue
		
		# Otherwise get the preprint
		else:
			preprint_path = get_preprint(submission_path, texs)
			if preprint_path:
				preprints.append(preprint_path)
			else:
				corrupt_submissions.append(arxiv_id)
	
	print('TEX files: ' + str(texfile_count))
	print('Submissions: ' + str(submission_count))
	print('Preprints: ' + str(len(preprints)))
	print('Empty submissions: ' + str(len(empty_submissions)))
	print('Potentially corrupt submissions: ' + str(len(corrupt_submissions)))

	return preprints

def get_outpath(tex_path):
	'''
	Returns the filepath for a XML file,
	based on the given TEX filepath. 
	'''
	
	path_parts = pathlib.Path(tex_path).parts
	arxiv_id = path_parts[2]
	outpath = 'xml/' + arxiv_id + '.xml'
	return outpath

def get_preprints_to_convert(key):
	'''
	Returns a list of strings. Each string 
	is a path to a TEX file within given folder
	that has not yet been converted to XML.
	'''
	
	preprints = get_all_preprints_from_tarfile(key)
	preprints_to_convert = []
	
	for tex_path in preprints:
		outpath = get_outpath(tex_path)
		logfile_path = 'logs/' + os.path.splitext(os.path.basename(tex_path))[0] + '.txt'
		if not os.path.isfile(outpath):
		#and not os.path.isfile(logfile_path):
			preprints_to_convert.append(tex_path)
			
	print(str(len(preprints_to_convert)) + ' preprints to be converted...')
	return preprints_to_convert


def get_preprint(submission_path, texs):
	'''
	Identifies the preprint within a given submission. 
	
	Parameters
	----------
	submission_path : str
		Filepath to submission directory
	texs : list of str
		Filepaths to all TEX files within submission directory
	'''
	preprint = None
	
	# If submission contains only one file, this is the preprint
	if len(texs) == 1:
		preprint = texs[0]
	# If submission contains ms.tex or main.tex, this is the preprint
	elif 'ms.tex' in texs:
		preprint = submission_path + '/' + 'ms.tex'
	elif 'main.tex' in texs:
		preprint = submission_path + '/' + 'main.tex'
	# Otherwise, iterate through each .tex looking for \documentclass or \documentstyle
	else: 
		for tex_path in texs: 
			with open(tex_path, 'rb') as f: 
				data = f.readlines()
				r = re.compile(b'(.*\\\\documentclass.*)|(.*\\\\documentstyle.*)')
				if len(list(filter(r.match, data))) > 0:
					preprint = tex_path
					break
	
	return preprint

def work(in_file):
	'''
	Defines the work to be done in each multiprocessing worker.
	'''
	
	# Get paths for converted file & logfile
	out_file = get_outpath(in_file)
	logfile_path = 'logs/' + os.path.splitext(os.path.basename(out_file))[0] + '.txt'
	
	# Try conversion, logging command line output
	try:
		print('{} is converting {}...'.format(mp.current_process(), in_file))
		with open(logfile_path, 'w') as logfile:
			sp.call(['latexml', '--dest=' + out_file, in_file], timeout=240, stderr=logfile)
		print('Writing logfile for ' + in_file)
	# If conversion has timed out, stop it (or it will eat up memory)
	# (this usually happens if latexml hangs recursively, as with 
	# latex/arXiv_src_1009_002/1009.1724/15727_eger.tex)
	except sp.TimeoutException:
		print('---x Conversion failed: {}'.format(in_file))
		sp.kill()
	return 0

def convert(key):
	# Specify files that need work 
	tasks = get_preprints_to_convert(key)
	
	# Set up the parallel task pool to use all available processors
	pool = mp.Pool(processes=mp.cpu_count())
 
	# Run the jobs
	try:
		pool.map(work, tasks)
	except KeyboardInterrupt:
		print('\nYou interrupted the script!')
		pool.terminate()
		exit(1)
	except Exception as e:
		print('\nSomething unknown went wrong: ' + e)
		pool.terminate()
		exit(1)
	pool.close()
	pool.join()


if __name__ == "__main__":
	# Get identifiers for astro-ph preprints
	m = Metadata(update=False)
	print('Identifiers collected: {}'.format(len(m.identifiers)))

	# Connect to Google Drive
	g = Gdrive() 
	gdrive_tarfiles = g.get_tarfiles()
	print('Tarfiles on Google Drive: {}'.format(len(gdrive_tarfiles)))

	# Connect to Amazon S3 and get page iterator
	s3 = Amazon_S3()

	# Download preprints
	for page in s3.get_page_iterator():
		for file in page['Contents']:
			key = file['Key']
			if key.endswith('.tar'):
				# Check if tarfile exists in Google Drive
				gtar = None
				for gfile in gdrive_tarfiles:
					if gfile.metadata['title'] == os.path.basename(key):
						gtar = gfile
				# If tarfile is in Google Drive, download and process it
				if gtar:
					#g.download_file(gtar, key)
					#extract(key, m.identifiers)
					print(key)
					print(os.path.basename(key))
					convert(''.join(['latex/', os.path.splitext(os.path.basename(key))[0]]))
					# Extract
					# Convert
					# os.remove(key)
				else:
					# download from s3
					# extract
					# convert
					# upload to google drive
					# os.remove(key)
					pass
