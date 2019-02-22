import datetime, os, pandas as pd, numpy as np, urllib, time
from bs4 import BeautifulSoup


class Metadata(object):
    '''
    '''

    identifiers = None
    metadata_filepath = None

    def request_bulk_metadata(self, date_of_last_request):
        '''
        Requests bulk metadata from OAI2. 
        Returns (rows, requestDate) where 
        '''

        rows = []
        resumptionToken = 'placeholder'
        url = 'http://export.arxiv.org/oai2?verb=ListRecords&set=physics:astro-ph&metadataPrefix=arXiv'
        results = None

        # If we have specified the date of the last request, add it to the URL
        if date_of_last_request:
            url += '&from=' + date_of_last_request.strftime('%Y-%m-%d')

        # Continue requesting until we are not given any more resumption tokens
        while resumptionToken is not None:
            # Send request and receive results, waiting specified time if necessary
            while results == None:
                try:
                    print('Requesting: ' + url)
                    results = urllib.request.urlopen(url).read()
                except urllib.error.HTTPError as e:
                    wait = int(e.headers.get('Retry-After'))
                    print('HTTPError: Waiting ' + str(wait) + 's to retry requesting metadata...')
                    time.sleep(wait)

            # Parse with Beautiful Soup
            soup = BeautifulSoup(results, 'xml')
            records = soup.find_all('record')
            for record in records:
                # Get header data
                identifier = record.find('identifier')
                datestamp = record.find('datestamp')
                spec = record.find('setSpec')

                # Get metadata
                filename = record.find('id')
                created = record.find('created')
                updated = record.find('updated')
                authors = []
                for author in record.find_all('author'):
                    forenames = author.forenames
                    keyname = author.keyname
                    if forenames and keyname:
                        authors.append(author.forenames.text.strip() + ' ' + author.keyname.text.strip())
                author_str = ', '.join(authors)
                title = record.find('title')
                categories = record.find('categories')
                journal = record.find('journal-ref')
                doi = record.find('doi')
                abstract = record.find('abstract')
                comments = record.find('comment')

                # Save current record as a row in the table
                row = {
                    'identifier': getattr(identifier, 'text', None),
                    'filename': getattr(filename, 'text', None),
                    'spec': getattr(spec, 'text', None),
                    'title': getattr(title, 'text', None),
                    'datestamp': getattr(datestamp, 'text', None),
                    'created': getattr(created, 'text', None),
                    'updated': getattr(updated, 'text', None), # may have more than one instance that we're missing
                    'authors': author_str,
                    'categories': getattr(categories, 'text', None),
                    'journal': getattr(journal, 'text', None),
                    'doi': getattr(doi, 'text', None),
                    'abstract': getattr(abstract, 'text', None),
                    'comments': getattr(comments, 'text', None)
                }
                rows.append(row)

            # Get resumption token if provided
            resumptionToken = soup.find('resumptionToken')

            # Continue if we have resumption token
            if resumptionToken is not None:
                print('Status: ' + str(int(resumptionToken['cursor']) + 1) + '—' + str(len(rows)) + '/' + str(resumptionToken['completeListSize']) + '...')
                resumptionToken = resumptionToken.text
                url = 'http://export.arxiv.org/oai2?verb=ListRecords&resumptionToken=' + resumptionToken
                time.sleep(20) # avoid 503 status
            else:
                # Otherwise, obtain date of last request and the while loop ends here
                request_date = soup.find('responseDate').text
            
        return rows, request_date


    def update(self):
        '''
        Checks if an update is needed. If it is needed, gathers 
        '''
        if os.path.exists(self.metadata_filepath):
            # If the metadata file exists, load it into a data frame
            existing_metadata_df = pd.read_csv(self.metadata_filepath, 
                                               dtype={'filename': str,
                                                      'filename_parsed': str,
                                                      'identifier': str,
                                                      'updated': str,
                                                      'doi': str}, 
                                               parse_dates=['date_retrieved'])
            # Get the date of the last request
            date_of_last_request = existing_metadata_df['date_retrieved'].max()
            print(self.metadata_filepath + ' last updated on ' + date_of_last_request.strftime('%Y-%m-%d'))
            print('Updating...')
            # Send a request to access metadata since that date
            date_to_request = date_of_last_request + datetime.timedelta(days=1)
            records, request_date = self.request_bulk_metadata(date_to_request)
            # Create data frame for records to specify additional info
            if len(records) > 0:
                print('Number of new records found: ' + str(len(records)))
                records_df = pd.DataFrame(records)
                records_df['date_retrieved'] = np.full(len(records_df), request_date)
                records_df['filename_parsed'] = existing_metadata_df['filename'].str.replace('/', '')
                # Update metadata file
                metadata_df = pd.concat([existing_metadata_df, records_df], axis=0, sort=True, ignore_index=True)
                metadata_df.to_csv(self.metadata_filepath, index=False)
                print('Metadata has been updated.')
            else: 
                print('No additional records found. Metadata is up to date.')
        else:
            # If the metadata file doesn't exist, request all metadata
            print(self.metadata_filepath + ' is being created...')
            records, request_date = self.request_bulk_metadata(None)
            # Load records into data frame
            metadata_df = pd.DataFrame(records)
            # Add a column to specify additional info
            metadata_df['date_retrieved'] = np.full(len(metadata_df), request_date)
            metadata_df['filename_parsed'] = metadata_df['filename'].str.replace('/', '')
            # Save it to CSV
            metadata_df.to_csv(self.metadata_filepath, index=False)
            print('Metadata has been saved.')


    def get_identifiers(self):
        # Grab identifiers from metadata
        metadata_df = pd.read_csv(self.metadata_filepath, 
                                   dtype={'filename': str,
                                          'filename_parsed': str,
                                          'identifier': str,
                                          'updated': str,
                                          'doi': str}, 
                                   parse_dates=['date_retrieved'])
        self.identifiers = metadata_df['filename_parsed']

    def __init__(self, update=False):
        self.metadata_filepath = 'arxiv_metadata_astroph.csv'
        # Automatically check for any updates
        if update:
            self.update()
        self.get_identifiers()


