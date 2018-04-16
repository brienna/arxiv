import subprocess, os, json, re
from bs4 import BeautifulSoup, NavigableString

def convert_tex_to_xml():
    """
    Converts downloaded .tex files to .xml if they haven't already been converted. 
    Requires latexml package: $ brew install latexml
    """

    for file_to_convert in os.listdir("latex"):
        filename, file_extension = os.path.splitext(file_to_convert)
        converted_filepath = "xml/" + filename + ".xml"
        if file_extension == ".tex" and not os.path.exists(converted_filepath):
            # Run latexml on command line
            print(subprocess.run(["latexml", "--dest=" + converted_filepath, "latex/" + file_to_convert]))

def parse():
    """
    Parses converted .xml files for word content.
    """

    stopwords = json.load(open('stopwords.json', 'r'))
    corpus = open('corpus.txt', 'w')
    num = 0

    for file in os.listdir("xml"):
        if file.endswith('.xml'):
            print('\nParsing ' + file + '...')
            with open("xml/" + file) as f:
                soup = BeautifulSoup(f, "xml")
                document = soup.find('document')
                # If .xml file represents an actual article, as specified by \document tag
                if document:
                    ###### Generate a smaller corpus
                    # desired = document.find('title', recursive=False) # recurisve, only searches top level elements
                    desired = document.find('abstract', recursive=False)
                    if desired:
                        # Don't handle any math right now
                        math = desired.find('Math')
                        if math:
                            math.decompose()
                        # Get text, remove newlines caused by nested TeX elements, and lowercase
                        text = desired.get_text().replace('\n', ' ').lower()
                        text.lower()
                        # Remove stopwords
                        cleaned_text = ' '.join([word for word in text.split() if word not in stopwords])
                        # For titles only
                        #if not desired.endswith('.'):
                        #    sentence = sentence + '.'
                        corpus.write('\n\n' + cleaned_text)
                        print(cleaned_text)
                        num += 1
                    ######
                    # sections = soup.find_all('section')
                    # print('sections: ' + str(len(sections)))
                    # for section in sections:
                    #     # Process citations
                    #     citations = section.find_all('cite')
                    #     for citation in citations:
                    #         # Render inline citations
                    #         if citation.has_attr('class') and citation['class'] == 'ltx_citemacro_citet':
                    #             # Get ref #
                    #             citet = citation.bibref['bibrefs']
                    #             # Using ref #, find inline citation in bibliography
                    #             bib_item = soup.find('bibitem', attrs={'key': citet})
                    #             if bib_item: 
                    #                 authors = bib_item.find('bibtag', attrs={'role': 'refnum'}).string
                    #             else: 
                    #                 print('Citation missed: ' + citet) # account for array of citations in aldering.xml
                    #             # Replace citation tag with in-text citation str
                    #             citation.replace_with(NavigableString(authors))
                    #         # Otherwise remove citation for now
                    #         else:
                    #             citation.decompose()
                    #     # Remove titles, footnotes, tables, figures (although converting to XML should not include them), and captions
                    #     titles = section.find_all('title')
                    #     for title in titles:
                    #         title.decompose()
                    #     footnotes = section.find_all('note')
                    #     for footnote in footnotes:
                    #         footnote.decompose()
                    #     tables = section.find_all('tabular')
                    #     for table in tables:
                    #         table.decompose()
                    #     captions = section.find_all('caption')
                    #     for caption in captions:
                    #         caption.decompose()
                    #     figures = section.find_all('figure')
                    #     for figure in figures:
                    #         figure.decompose()
                    #     # Remove inline math for now, until we fix formatting
                    #     maths = section.find_all('Math')
                    #     for math in maths:
                    #         math.decompose()
                    #     # Ignore errors in converting, e.g. authors miswrote \citep as \pcite
                    #     errors = section.find_all('ERROR')
                    #     for error in errors:
                    #         error.decompose()
                        # Append document to corpus (EDIT TO EXCLUDE TITLES)
                    #    corpus.write(section.get_text())
    print('\n\nDocuments: ' + str(num))
    corpus.close()
    stopwords.close()

if __name__ == '__main__':
    # Convert the downloaded tex files to xml, to help with parsing
    # convert_tex_to_xml()
    # Parse titles
    parse()



