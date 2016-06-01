# CS123
# Campaign Donation MRJob Project

# This file takes a JSON of resolved entities of the form {instance:
# authoritative_name}, reads the full dataset, then extracts relevant 
# information for each authoritative name and prints to csv format.

from mrjob.job import MRJob
from mrjob.protocol import ReprValueProtocol
import csv
from fuzzywuzzy import fuzz
import json
import re
import os

# Column indices for slicing
ID = 0
AMOUNT = 8
DATE = 9
CONTRIBUTOR_NAME = 10
CONTRIBUTOR_TYPE = 12
CONTRIBUTOR_EMPLOYER = 14
ORGANIZATION = 21
PARENT_ORGANIZATION = 23
RECIPIENT_NAME = 25
CANDIDATE_PARTY = 27
SEAT = 36
RESULT = 41

class build_corporate_donations(MRJob):
    '''
    This job builds a dataset for corporate donations.
    '''
    OUTPUT_PROTOCOL = ReprValueProtocol

    def configure_options(self):
        '''
        Makes a file available to mapper.
        
        Use: Add --ancillary='FILE-PATH' as an option when running MRJob.
        '''
        super(build_corporate_donations, self).configure_options()
        self.add_file_option('--ancillary')
    
    def similarity_score(self, string1, string2):
        '''
        Performs an analysis to determine the similarity of two strings.
        '''
        stopwords = [ 'a', 'in', 'for', 'and', 'the', 'as', 'at', 'by', 
         'from', 'into', 'to', 'of', 'on', 'off', 'our', 'that', 
         'so', 'own', 'out', 'communication', 'communications' ,'inc', 
         'incorporated', 'company', 'corporation', 'co', 
         'enterprise', 'enterprises','group', 'industries', 'corp', 'llc', 
         'llp', 'international', 'product', 'products'   
         'technologies', 'technology', 'holdings', 'holding', 'global', 
         'financial', 'service', 'services', 'resource', 'resources']
        string1 = re.sub('[^a-zA-Z\d\s]','',string1).lower()
        string2 = re.sub('[^a-zA-Z\d\s]','',string2).lower()
        string1 = [word for word in string1.split() if word not in stopwords]
        string2 = [word for word in string2.split() if word not in stopwords]
        string1 = "".join(string1)
        string2 = "".join(string2)
        return fuzz.ratio(string1, string2)
    
    def fields(self, line):
        '''
        Reads and strips line.
        '''
        yield_value = False
        try:
            # Reads line & eliminates weird characters, skips header
            rdr = csv.reader([line])
            columns = rdr.next()
            for i in range(len(columns)):
                columns[i] = columns[i].strip("'\"\/").upper()
            if columns[0] != 'id':
                donor_name = columns[CONTRIBUTOR_NAME]
                organization = columns[ORGANIZATION]
                parent = columns[PARENT_ORGANIZATION]
                recipient = columns[RECIPIENT_NAME]
                party = columns[CANDIDATE_PARTY]
                date = columns[DATE]
                amount = columns[AMOUNT]
                seat = columns[SEAT]
                result = columns[RESULT].replace("\\", "")
                result = result.replace("'", "")
            else:
                donor_name = None
                organization = None
                parent = None
                recipient = None
                party = None
                date = None
                amount = None
                seat = None
                result = None
            if organization.lower() != parent.lower() and parent in \
             self.entity_dictionary:
                organization = self.entity_dictionary.get(parent)
            elif organization in self.entity_dictionary: 
                organization = self.entity_dictionary.get(organization)
            recipient = self.entity_dictionary.get(recipient, None)
            
        except Exception as e: 
            print e
            donor_name = None
            organization = None
            recipient = None
            party = None
            date = None
            amount = None
            seat = None
            result = None
        
        return (organization, recipient, party, date, amount, seat, result, donor_name)
    
    def mapper_init(self):
        '''
        Holds entity dictionary in memory for authoritative name lookup.
        '''
        with open(self.options.ancillary, 'rU') as f:
            self.entity_dictionary = json.load(f)
    
    def mapper(self, _, line):
        '''
        Reads line and concats strings. 
        '''
        try: 
            line.decode('ascii')
        except: 
            pass  
        
        organization, recipient, party, date, amount, seat, result, donor_name = self.fields(line)
        
        if organization != None and self.similarity_score(donor_name, organization) > 90:
            year = date.split('-')[0]
            month = date.split('-')[1]
            print [organization, recipient, party, seat, result, month, year]
            key = ','.join([organization, recipient, party, seat, result, month, year])
        
            yield key, amount
        
    def reducer(self, key, amount):
        '''
        '''
        total = sum(amount)
        rv = ','.join([key, total])
        yield None, rv
        
        
if __name__ == '__main__':
    build_corporate_donations.run()
