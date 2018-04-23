import subprocess, os, json, re
from bs4 import BeautifulSoup, NavigableString

def convert_tex_to_xml():
    """
    Converts downloaded .tex files to .xml if they haven't already been converted. 
    Requires latexml package: $ brew install latexml
    """

    # For each file in latex directory
    for file_to_convert in os.listdir("latex"):
        filename, file_extension = os.path.splitext(file_to_convert)
        converted_filepath = "xml/" + filename + ".xml"
        # Confirm it is latex and that it hasn't already been converted
        if file_extension == ".tex" and not os.path.exists(converted_filepath):
            # Run latexml on command line to convert latex file to xml file
            print(subprocess.run(["latexml", "--dest=" + converted_filepath, "latex/" + file_to_convert]))

def parse():
    """
    Parses converted .xml files for word content.
    """

    # Initialize trackers
    num_of_abstracts = 0
    num_of_fulltexts = 0

    # Open corpora for writing
    abstracts_corpus = open('abstracts_corpus.txt', 'w')
    fulltexts_corpus = open('fulltexts_corpus.txt', 'w')

    # For each xml file
    for file in os.listdir("xml"):
        if file.endswith('.xml'):
            print('\nParsing ' + file + '...')
            with open("xml/" + file) as f:
                soup = BeautifulSoup(f, "xml")
                document = soup.find('document')

                # If .xml file represents an actual article (specified by \document tag)
                if document:
                    # Get abstract from document
                    abstract = getAbstract(document)
                    # Add abstract to corpus 
                    if abstract is not None:
                        print('Adding abstract from ' + file)
                        abstracts_corpus.write('\n\n' + abstract)
                        num_of_abstracts += 1

                    # Get fulltext from file
                    # fulltext = getFullText(soup)
                    # # Add fulltext to corpus
                    # if fulltext is not None:
                    #     print('Adding fulltext from ' + file)
                    #     fulltexts_corpus.write(fulltext)
                    #     num_of_fulltexts += 1

    print('\n\nAbstracts: ' + str(num_of_abstracts))
    print('\n\nFull texts: ' + str(num_of_fulltexts))
    
    abstracts_corpus.close()
    fulltexts_corpus.close()


def getFullText(soup):
    """ 
    Returns cleaned full body text from passed soup, a BeautifulSoup soup of a .xml file.
    """

    fulltext = ""

    sections = soup.find_all('section')
    print('sections: ' + str(len(sections)))

    for section in sections:
        # Process citations
        citations = section.find_all('cite')
        for citation in citations:
            # Render inline citations by fetching author info from bibliography
            if citation.has_attr('class') and citation['class'] == 'ltx_citemacro_citet':
                # Get bibliography reference
                citet = citation.bibref['bibrefs']
                # Using reference, get authors from bibliography
                bib_item = soup.find('bibitem', attrs={'key': citet})
                if bib_item: 
                    authors = bib_item.find('bibtag', attrs={'role': 'refnum'}).string
                    # Replace citation tag with in-text citation str
                    citation.replace_with(NavigableString(authors))
                else: 
                    print('Citation missed: ' + citet) # account for array of citations in aldering.xml
            # If not inline citation, remove citation for now
            else:
                citation.decompose()
        # Remove titles, footnotes, tables, figures (although converting to XML should not include them), and captions
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
        # Remove inline math for now
        maths = section.find_all('Math')
        for math in maths:
            math.decompose()
        # Ignore errors in converting, e.g. authors miswrote \citep as \pcite
        errors = section.find_all('ERROR')
        for error in errors:
            error.decompose()

        fulltext = fulltext + section.get_text()
    
    return fulltext


def getAbstract(document):
    """
    Returns cleaned abstract from passed document, a BeautifulSoup 'document' node.
    Returns none if no abstract found.
    """

    stopwords = json.load(open('stopwords.json', 'r'))
    text = ""

    abstract = document.find('abstract', recursive=False)
    
    if abstract:
        # Don't handle any math right now
        math = abstract.find('Math')
        if math:
            math.decompose()

        # Get text, remove newlines caused by nested TeX elements, and lowercase
        text = abstract.get_text().replace('\n', ' ').lower()
        text.lower()

        # Remove stopwords
        cleaned_text = ' '.join([word for word in text.split() if word not in stopwords])
        
        return cleaned_text
        # Add cleaned abstract to corpus
        # corpus.write('\n\n' + cleaned_text)

    return None


if __name__ == '__main__':
    """Runs if script called on command line"""
    
    # Convert the downloaded tex files to xml, to help with parsing (SLOW)
    # convert_tex_to_xml()

    # Parse titles
    parse()



