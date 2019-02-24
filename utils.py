import tarfile
import gzip
import shutil
import os
import glob
import re
import pathlib
import zipfile
import subprocess as sp


def confirmDir(dir_name):
	if not os.path.isdir(dir_name):
		os.makedirs(dir_name)


def extract(filepath, identifiers):
	'''
	Extracts astro-ph submissions from given tar filepath.
	Logs which submissions belong to particular tarfile.
	'''

	# Quit if given file is not tarfile
	if not tarfile.is_tarfile(filepath):
		print('can\'t unzip {}, not a .tar file'.format(filepath))
		return

	total_submissions_extracted = 0
	tar_dir = 'latex/' + os.path.splitext(os.path.basename(filepath))[0] 
	confirmDir(tar_dir)
		
	# Open tarfile, read-only
	print('Extracting {}'.format(filepath))
	tar = tarfile.open(filepath)
	# Iterate over submissions, extracting only those that belong to the astro-ph category, 
	# logging which submissions belong to which tarfile
	with open(tar_dir + '.txt', 'w+') as logfile:
		logfile.write('TARFILE: {}'.format(os.path.basename(filepath)))
		for submission in tar.getmembers():
			submission_id = os.path.splitext(os.path.basename(submission.name))[0]
			if submission.name.endswith('.gz') and identifiers.str.contains(submission_id).any():
				logfile.write('\n' + submission_id)
				submission_path = tar_dir + '/' + submission_id
				# Extract the submission as a .gzip
				try:    
					# Extract and convert to .zip
					gz_obj = tar.extractfile(submission)
					gz = tarfile.open(fileobj=gz_obj)
					zipf = zipfile.ZipFile(file=submission_path + '.zip', mode='a', compression=zipfile.ZIP_DEFLATED)                
								
					for m in gz: 
						f = gz.extractfile(m)
						if m.isdir():
							continue
						f_out = f.read()
						f_in = m.name
						zipf.writestr(f_in, f_out)
					zipf.close()
					gz.close()
					total_submissions_extracted += 1
				except tarfile.ReadError:
					confirmDir('temp')
					tar.extract(submission, 'temp')
					with gzip.open('temp/' + submission.name, 'rb') as f_in:
						with open(submission_path + '.tex', 'wb+') as f_out:
							shutil.copyfileobj(f_in, f_out)
							total_submissions_extracted += 1
	tar.close()
	# Delete the temporary folder for those wonky gz files
	shutil.rmtree('temp/', ignore_errors=True)
	print(filepath + ' extraction complete')
	print('Number of submissions obtained: ' + str(total_submissions_extracted))


def get_outpath(inpath):
	'''
	Returns the filepath for a XML file,
	based on the given TEX filepath. 
	'''

	path_parts = pathlib.Path(inpath).parts
	arxiv_id = os.path.splitext(path_parts[2])[0]
	confirmDir('xml')
	outpath = 'xml/' + arxiv_id + '.xml'
	return outpath


def get_submissions_to_convert(base_path):
	'''
	Returns a list of strings. Each string 
	is a path to a submission directory or .tex file within
	the tar directory that has not yet been converted to XML,
	or attempted to be converted (as evidenced by existence of logfile)
	'''
	
	submissions = glob.glob(base_path + '/*[.tex|.zip]')
	submissions_to_convert = []

	for submission_path in submissions:
		outpath = get_outpath(submission_path)
		logfile_path = 'logs/' + os.path.splitext(os.path.basename(submission_path))[0] + '.txt'
		if not os.path.isfile(outpath) and not os.path.isfile(logfile_path):
			submissions_to_convert.append(submission_path)

	print('{} submissions already converted, {} submissions still to be converted...'.format(len(submissions) - len(submissions_to_convert), len(submissions_to_convert)))
	return submissions_to_convert


def convert(tar_path):
	'''
	Converts submission into XML, calling 
	latexmlc --dest=[output_file] [input_file]
	Latexmlc will be able to extract ZIPs (not Tars unfortunately)
	https://github.com/brucemiller/LaTeXML/issues/1091
	'''

	confirmDir('logs')
	submissions = get_submissions_to_convert(tar_path)

	for submission in submissions:
		# Get its outpath
		outpath = get_outpath(submission)
		submission_id = os.path.splitext(os.path.basename(outpath))[0]
		logfile_path = 'logs/' + submission_id + '.txt'
		try:
			print('Converting {} to {}...'.format(submission, outpath))
			with open(logfile_path, 'w+') as logfile:
				sp.call(['latexmlc', '--dest=' + outpath, submission], timeout=240, stderr=logfile)
			print('Writing logfile for ' + submission_id)
		# If conversion has timed out, stop it (or it will eat up memory)
		# (this usually happens if latexml hangs recursively, as with 
		# latex/arXiv_src_1009_002/1009.1724/15727_eger.tex)
		except sp.TimeoutExpired:
			print('---x Conversion failed: {}'.format(submission))
			with open('logs/failed_conversions_log.txt', 'a+') as failed_conversions_logfile:
				failed_conversions_logfile.write(submission_id + '\n')
			sp.kill()
		except KeyboardInterrupt:
			# If I interrupt the conversion, remove the logfile so it can be reattempted
			print('Removing ' + logfile_path)
			os.remove(logfile_path)
			raise
		except Exception:
			print('Removing ' + logfile_path)
			os.remove(logfile_path)
			raise


