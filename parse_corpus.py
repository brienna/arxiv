
import os
import glob
import utils
from bs4 import BeautifulSoup


class Parser(object):

	def __init__(self):
		pass

	def parse(self, xml_path):
		'''
		Parses XML file at given path.
		'''

		fulltext = ''
		
		with open(xml_path) as xml:
			soup = BeautifulSoup(xml, 'xml')
			sections = soup.find_all('section')
			print('Sections: ' + str(len(sections)))

			for section in sections:
				# Process citations that have a class only
				citations = section.find_all('cite', {'class': True})
				for citation in citations:
					# Render inline citations by fetching author info from bibs
					if citation.name != None:
						if citation['class'] == 'ltx_citemacro_citet' or citation['class'] == 'ltx_citemacro_cite':
							bibref = citation.bibref['bibrefs']
							bib_item = soup.find('bibitem', attrs={'key': bibref})
							if bib_item: 
								authors = bib_item.find('bibtag', attrs={'role': 'refnum'})
								if authors != None and authors.text != None:
									# Replace citation tag with in-text citation str
									citation.replace_with(authors.text)
								else:
									print('Authors not found')
							else:
								print('Citation missed ' + bibref)
						elif citation['class'] == 'ltx_citemacro_citep':
							bibrefs = citation.bibref['bibrefs'] # looks like 'Hinshaw+2006,Hivon+2002,McEwen+2007'
							bibref_split = bibrefs.split(',')
							for bibref in bibrefs: 
								bib_item = soup.find('bibitem', attrs={'key': bibref})
					# Otherwise, remove citation from parsed text
					else:
						citation.decompose()

				# Remove stuff
				titles = section.find_all('title')
				for title in titles:
					title.decompose()
				footnotes = section.find_all('note')
				for footnote in footnotes:
					footnote.decompose()
				tables = section.find_all('tabular')
				for table in tables:
					table.decompose()
				captions = section.find_all('caption')
				for caption in captions:
					caption.decompose()
				figures = section.find_all('figure')
				for figure in figures:
					figure.decompose()
				tags = section.find_all('tags')
				for tag in tags:
					tag.decompose()
				# Remove inline math for now
				maths = section.find_all('Math')
				for math in maths:
					math.decompose()
				# Ignore errors in converting, e.g. author miswrote \citep as \pcite
				errors = section.find_all('ERROR')
				for error in errors:
					error.decompose()

				fulltext += section.get_text()

		return fulltext


	def main(self):

		# For each xml file
		utils.confirmDir('corpus')
		xml_files = glob.glob('xml/*[.xml]')
		for xf in xml_files:
			arxiv_id = os.path.splitext(os.path.basename(xf))[0]
			# If XML file has already been parsed, don't parse again
			if os.path.isfile('corpus/' + arxiv_id + '.txt'):
				#print('{} has already been parsed.'.format(arxiv_id))
				continue
			# Otherwise parse it
			else:
				#print('Parsing {}...'.format(arxiv_id))
				with open('corpus/' + arxiv_id + '.txt', 'w+') as fulltext_file: 
					fulltext = self.parse(xf)
					fulltext_file.write(fulltext)
			

if __name__ == '__main__':
	p = Parser()
	p.main()
