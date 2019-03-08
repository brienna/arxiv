
import os
import glob
import utils
import re
from bs4 import BeautifulSoup


class Parser(object):
	soup = None

	def __init__(self):
		pass
	
	def remove_stuff(self, section):
		titles = section.find_all('title', recursive=True)
		for title in titles:
			title.decompose()
		footnotes = section.find_all('note', recursive=True)
		for footnote in footnotes:
			footnote.decompose()
		tables = section.find_all('tabular', recursive=True)
		for table in tables:
			table.decompose()
		captions = section.find_all('caption', recursive=True)
		for caption in captions:
			caption.decompose()
		captions2 = section.find_all('toccaption', recursive=True)
		for caption2 in captions2:
			caption2.decompose()
		figures = section.find_all('figure', recursive=True)
		for figure in figures:
			figure.decompose()
		tags = section.find_all('tags', recursive=True) # includes footnotes
		for tag in tags:
			tag.decompose()
		# Remove inline math for now
		maths = section.find_all('Math', recursive=True)
		for math in maths:
			math.decompose()
		# Ignore errors in converting, e.g. author miswrote \citep as \pcite
		errors = section.find_all('ERROR', recursive=True)
		for error in errors:
			error.decompose()
		

	def process_citations(self, section):
		# Process citations that have a class only
		citations = section.find_all('cite', {'class': True})
		for citation in citations:
			# Render inline citations by fetching author info from bibs
			if citation.name != None:
				if citation['class'] == 'ltx_citemacro_citet' or citation['class'] == 'ltx_citemacro_cite':
					bibref = citation.bibref['bibrefs']
					bib_item = self.soup.find('bibitem', attrs={'key': bibref})
					if bib_item: 
						# Try to find authors in bibtag
						#refnum = bib_item.find('bibtag', attrs={'role': 'refnum'}, recursive=True)
						#if refnum == None:
							# refnum = bib_item.find('tag', attrs={'role': 'refnum'})
						authors = bib_item.find(attrs={'role': 'refnum'}, recursive=True)
						print(authors)
						if authors != None and authors.text != None:
							# if the authors text is only numeric, don't use
							regex = re.compile(r'^\\d*$')
							if regex.match(authors.text):
								print('Excluding numeric reference: {}'.format(authors))
							else:
								# Replace citation tag with in-text citation str
								citation.replace_with(authors.text)
						else:
							print(bib_item)
							print('Authors not found')
					else:
						print('Citation missed ' + bibref)
				elif citation['class'] == 'ltx_citemacro_citep':
					bibrefs = citation.bibref['bibrefs'] # looks like 'Hinshaw+2006,Hivon+2002,McEwen+2007'
					bibref_split = bibrefs.split(',')
					for bibref in bibrefs: 
						bib_item = self.soup.find('bibitem', attrs={'key': bibref})
			# Otherwise, remove citation from parsed text
			else:
				citation.decompose() 

	def parse(self, xml_path):
		'''
		Parses XML file at given path.
		'''

		fulltext = ''

		with open(xml_path) as xml:
			self.soup = BeautifulSoup(xml, 'xml')
			sections = self.soup.find_all('section')
			
			if not sections: 
				paragraphs = self.soup.find_all('para')
				print('Paragraphs: ' + str(len(paragraphs)))
				if paragraphs:
					for p in paragraphs:
						#self.process_citations(p)
						citations = p.find_all('cite')
						for citation in citations:
							citation.decompose()
						fulltext += p.get_text()
			else: 
				print('Sections: ' + str(len(sections)))
				for section in sections:
					#self.process_citations(section)
					citations = section.find_all('cite')
					for citation in citations:
						citation.decompose()
					self.remove_stuff(section)
					fulltext += section.get_text()

		return fulltext


	def main(self):

		# For each xml file
		utils.confirmDir('corpus')
		xml_files = glob.glob('xml/*[.xml]')
		print('XML files: {}'.format(len(xml_files)))
		for xf in xml_files:
			arxiv_id = os.path.splitext(os.path.basename(xf))[0]
			# If XML file has already been parsed, don't parse again
			if os.path.isfile('corpus/' + arxiv_id + '.txt'):
				print('{} has already been parsed.'.format(arxiv_id))
				continue
			# Otherwise parse it
			else:
				print('Parsing {}...'.format(arxiv_id))
				with open('corpus/' + arxiv_id + '.txt', 'w+') as fulltext_file: 
					fulltext = self.parse(xf)
					fulltext_file.write(fulltext)
			

if __name__ == '__main__':
	p = Parser()
	p.main()
