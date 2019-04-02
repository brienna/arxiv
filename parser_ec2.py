import os
import glob
import utils
import re
from bs4 import BeautifulSoup
import nltk
import numpy as np
import traceback, sys
import multiprocessing as mp
import time

class Parser(object):
    soup = None
    parenthetical_citations = 0
    intext_citations = 0
    xml_folder = 'xml'

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
        tags2 = section.find_all('tag', recursive=True)
        for tag in tags2:
            tag.decompose()
                
        # For math, if 'meaning' or 'name' attr is there, use it
        maths = section.find_all('Math', recursive=True)
        for math in maths:
            
            #xmtoks = math.find_all('XMTok', recursive=True)
            #for xmtok in xmtoks:
            #    if xmtok.has_attr('name'): ### FIX
            #        xmtok.replace_with(xmtok['name'])
            #    elif xmtok.has_attr('meaning'): ### FIX
            #        xmtok.replace_with(xmtok['meaning'])
            #    else: 
            #        print(xmtok)
            #        xmtok.decompose()
            math.replace_with(' latex_metatoken ')
        # Ignore errors in converting, e.g. author miswrote \citep as \pcite
        errors = section.find_all('ERROR', recursive=True)
        for error in errors:
            error.decompose()
            
    def render_authors(self, citation, bib_item):
        intext_citations = 0
        
        authors = bib_item.find(attrs={'role': 'refnum'}, recursive=True)
        if authors != None and authors.text != None:
            # If the authors text is numeric only, don't use
            regex = re.compile(r'^[(]?\d*[)]?$')
            if regex.match(authors.text.strip()):
                self.parenthetical_citations += 1
            else:
                # Replace citation tag with in-text citation string
                citation.replace_with(authors.text)
                self.intext_citations += 1
        else:
            print('Authors not found')
            
    def process_citations(self, section):        
        # Process only citations that have a class 
        citations = section.find_all('cite', {'class': True})
        for citation in citations:
            if citation.name != None:
                # Get rid of parenthetical citations
                if citation['class'] == 'ltx_citemacro_citep':
                    citation.decompose()
                    self.parenthetical_citations += 1
                # Process in-text citations
                elif citation['class'] == 'ltx_citemacro_citet' or citation['class'] == 'ltx_citemacro_cite':
                    bibref = citation.bibref['bibrefs']
                    bib_item = self.soup.find('bibitem', attrs={'key': bibref})
                    if bib_item:
                        self.render_authors(citation, bib_item)
                    else: 
                        # Decompose list of authors which usually indicates parenthetical citations
                        # print('Could not find reference for ' + citation['class'] + ': ' + bibref)
                        citation.decompose()
                        self.parenthetical_citations += 1
                        

    def parse(self, xml_path):
        '''
        Parses XML file at given path.
        '''

        fulltext = ''

        with open(xml_path) as xml:
            self.soup = BeautifulSoup(xml, 'xml')
            sections = self.soup.find_all('section')
            print('Sections: ' + str(len(sections)))
            
            if not sections: 
                paragraphs = self.soup.find_all('para')
                print('Paragraphs: ' + str(len(paragraphs)))
                if paragraphs:
                    for p in paragraphs:
                        self.process_citations(p)
                        self.remove_stuff(p)
                        fulltext += p.get_text()
            else:    
                for section in sections:
                    self.process_citations(section)
                    self.remove_stuff(section)
                    fulltext += section.get_text()
        
        # print('Num parenthetical citations removed: ' + str(self.parenthetical_citations))
        # print('Num in-text citations rendered: ' + str(self.intext_citations))
        return fulltext
    
    
    def cleanse(self, doc):
        # Convert to lowercase
        doc = doc.lower()
        # Tokenize alphanumeric characters only, 
        # removing punctuation, 
        # changing all numbers to <num> metatoken
        tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
        num_pattern = re.compile(r'^\d*$')
        tokens = ['<num>' if num_pattern.match(x) else '<latex>' if x == 'latex_metatoken' else x for x in tokenizer.tokenize(doc)]
        return tokens
        
        



def work(xf):
    print('{} is working on {}...'.format(mp.current_process(), xf))
    try:
        p = Parser()
        # Confirm 'corpus' dir exists
        utils.confirmDir('corpus')

        # Get id of xml file
        arxiv_id = os.path.splitext(os.path.basename(xf))[0]
        npf = 'corpus/' + arxiv_id + '.npy'
        # If XML file has already been parsed, don't parse again
        if os.path.isfile(npf):
            print('{} has already been parsed.'.format(arxiv_id))
        else:
            print('Parsing {}...'.format(arxiv_id))
            fulltext = p.parse(xf)
            tokens = p.cleanse(fulltext) # array
            np.save(npf, tokens)
            print('Saved ' + npf)
    except Exception as e:
        print('\nSomething went wrong: {}'.format(e))
        traceback.print_exc()
        
def main():
    # Set up the parallel task pool to use all available processors
    pool = mp.Pool(processes=mp.cpu_count())
    print('Executing with ' + str(mp.cpu_count()) + ' workers...')
    processes = []
    tasks = glob.glob('xml/*[.xml]')
    print(str(len(tasks)) + ' files to parse...')
    
    try:
        for task in tasks:
            p = mp.Process(target=work, args=(task,))
            processes.append(p)
            p.start()
        
        for process in processes:
            process.join()
    except Exception as e:
        print('Something went wrong: {}'.format(e))
        traceback.print_exc()
    finally:
        pool.close()
        pool.join()
        sys.stdout.flush()
        print('The end.')

if __name__ == '__main__':
    starttime = time.time()
    main()
    print('That took {} seconds'.format(time.time() - starttime))




    