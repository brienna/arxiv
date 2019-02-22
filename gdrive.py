from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os


class Gdrive(object):
	drive = None


	def connect(self):
		g_login = GoogleAuth()
		g_login.LocalWebserverAuth()
		self.drive = GoogleDrive(g_login)


	def download_file(self, file, title):
	    '''
	    Downloads given file from Google Drive.

	    Parameters
	    ----------
	    file : str
	        The file in the form of a GoogleFile object 
	    title : str
	        The filename of the file
	    '''
	        
	    # Ensure src directory exists 
	    if not os.path.isdir('src'):
	        os.makedirs('src')
	    
	    # Download file
	    print('Downloading ' + title + ' from Google Drive...')
	    file.GetContentFile(title) 
	    print('Successfully downloaded drive://arxiv/{} to {}'.format(os.path.basename(title), title))


	def get_tarfiles(self):
	    '''
	    Gets names of all tarfiles in arxiv folder on Google Drive. 
	    Returns list of strings, each string representing a name. 
	    If there is no folder or it is empty, an empty list is returned. 
	    '''
	    
	    tars = []
	    query = "'root' in parents and trashed=false and title='arxiv' and mimeType='application/vnd.google-apps.folder'"
	    arxiv_folder_id = self.drive.ListFile({'q': query}).GetList()[0].metadata['id']
	    
	    # If folder doesn't exist, create and upload it, exit (we will have to query everything from S3)
	    if not arxiv_folder_id:
	        print('Google Drive does not contain a folder named \'arxiv\'. Creating folder...')
	        arxiv_folder = self.drive.CreateFile({'title': 'arxiv', 
	                                    "mimeType": "application/vnd.google-apps.folder"}) 
	        arxiv_folder.Upload()
	        arxiv_folder_id = arxiv_folder['id']
	        print('Folder created.')
	    else:
	        # Get list of files in arxiv folder
	        tars = self.drive.ListFile({'q': "'" + arxiv_folder_id + "' in parents and trashed=false"}).GetList()
	        tars_str = [x.metadata['title'] for x in tars]
	        tars_str.sort()
	    
	    return tars


	def __init__(self):
		self.connect()

