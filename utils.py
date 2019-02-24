import tarfile, gzip, shutil, os, glob, re, pathlib, subprocess as sp


def confirmDir(dir_name):
	if not os.path.isdir(dir_name):
		os.makedirs(dir_name)


def extract(filepath, identifiers):
	'''
	Extracts astro-ph submissions from given tar filepath.
	Logs which submissions belong to particular tarfile.
	'''

	# Quit file extraction if given file is not tarfile
	if not tarfile.is_tarfile(filepath):
		print('can\'t unzip {}, not a .tar file'.format(filepath))

	total_submissions = 0
	tar_dir = 'latex/' + os.path.splitext(os.path.basename(filepath))[0] + '/'

	# Create .tar directory if it doesn't exist
	if not os.path.isdir(tar_dir):
		os.makedirs(tar_dir)
		
	# Open tarfile, read-only
	print('Extracting {}'.format(filepath))
	tar = tarfile.open(filepath)
	# Iterate over submissions, extracting only those that belong to the astro-ph category, 
	# logging which submissions belong to which tarfile
	confirmDir('logs')
	with open('logs/tarfile_submission_log.txt', 'a+') as logfile:
		logfile.write('\n\nTARFILE: {}'.format(os.path.basename(filepath)))
		for submission in tar.getmembers():
			# Create submission directory if it doesn't exist
			submission_id = os.path.splitext(os.path.basename(submission.name))[0]
			submission_path = tar_dir + '/' + submission_id
			if submission.name.endswith('.gz') and identifiers.str.contains(submission_id).any():
				logfile.write('\n' + submission_id)
				confirmDir(submission_path)
				try:
					gz_obj = tar.extractfile(submission) 
					gz = tarfile.open(fileobj=gz_obj) 
					gz.extractall(path=submission_path)
					total_submissions += 1
				except tarfile.ReadError:
					# Extract the entire .gz because we cannot read it using tarfile 
					# Note that these .gzs are single .tex files with no extension specified
					tar.extract(submission, path='temp')
					# Uncompress the .gz file using gzip instead and place it with the other .tex files
					with gzip.open('temp/' + submission.name, 'rb') as f_in:
						basename = os.path.splitext(os.path.basename(submission.name))[0]
						with open(tar_dir + submission_id + '/' + basename + '.tex', 'wb+') as f_out:
							shutil.copyfileobj(f_in, f_out)
							total_submissions += 1
	tar.close()
	# Delete the temporary folder for those wonky gz files
	shutil.rmtree('temp/', ignore_errors=True)
	print(filepath + ' extraction complete')
	print('Number of submissions obtained: ' + str(total_submissions))


def get_outpath(tex_path):
	'''
	Returns the filepath for a XML file,
	based on the given TEX filepath. 
	'''
	
	path_parts = pathlib.Path(tex_path).parts
	arxiv_id = path_parts[2]
	outpath = 'xml/' + arxiv_id + '.xml'
	return outpath


def get_preprint(submission_path, candidates):
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
	if len(candidates) == 1:
		preprint = candidates[0]
	# If submission contains ms.tex or main.tex, this is the preprint
	elif 'ms.tex' in candidates:
		preprint = submission_path + '/' + 'ms.tex'
	elif 'main.tex' in candidates:
		preprint = submission_path + '/' + 'main.tex'
	# Otherwise, iterate through each .tex looking for subcandidates
	else: 
		subcandidates = []
		for candidate in candidates: 
			with open(candidate, 'rb') as f: 
				data = f.read()
				doc_regex = re.compile(b'(?m)^\\\\document(?:class|style).*')
				# If candidate contains \documentclass or \document style, also check for \input tag
				# NEED TO ADD THIS PART: IF the subcandidate is an argument of an input tag, remove it as a subcandidate
				if doc_regex.findall(data):
					subcandidates.append(candidate)
					preprint = candidate
					break 
	
	return preprint


def get_all_preprints(base_path):
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

	confirmDir('logs')
	with open('logs/corrupt_submissions_log.txt', 'a+') as corrupt_logfile:
		for submission in corrupt_submissions:
			corrupt_logfile.write(submission + '\n')
	with open('logs/empty_submissions_log.txt', 'a+') as empty_logfile:
		for submission in empty_submissions:
			empty_logfile.write(submission + '\n')

	return preprints


def get_preprints_to_convert(base_path):
	'''
	Returns a list of strings. Each string 
	is a path to a TEX file within given folder
	that has not yet been converted to XML.
	'''
	
	preprints = get_all_preprints(base_path)
	preprints_to_convert = []
	
	for tex_path in preprints:
		outpath = get_outpath(tex_path)
		logfile_path = 'logs/' + os.path.splitext(os.path.basename(tex_path))[0] + '.txt'
		if not os.path.isfile(outpath) and not os.path.isfile(logfile_path):
			preprints_to_convert.append(tex_path)
	
	print('{} preprints already converted, {} preprints still to be converted...'.format(len(preprints) - len(preprints_to_convert), len(preprints_to_convert)))	
	return preprints_to_convert


def convert(base_path):
	preprints = get_preprints_to_convert(base_path)
	confirmDir('logs')

	# Try conversion, logging command line output
	for preprint in preprints:
		# Get paths for converted file & logfile
		out_file = get_outpath(preprint)
		preprint_id = os.path.splitext(os.path.basename(out_file))[0]
		logfile_path = 'logs/' + preprint_id + '.txt'
		try:
			print('Converting {}...'.format(preprint))
			with open(logfile_path, 'w') as logfile:
				sp.call(['latexml', '--dest=' + out_file, preprint], timeout=240, stderr=logfile)
			print('Writing logfile for ' + preprint)
		# If conversion has timed out, stop it (or it will eat up memory)
		# (this usually happens if latexml hangs recursively, as with 
		# latex/arXiv_src_1009_002/1009.1724/15727_eger.tex)
		except sp.TimeoutExpired:
			print('---x Conversion failed: {}'.format(preprint))
			with open('logs/failed_conversions.txt', 'a+') as failed_conversions_logfile:
				failed_conversions_logfile.write(preprint_id + '\n')
			sp.kill()


