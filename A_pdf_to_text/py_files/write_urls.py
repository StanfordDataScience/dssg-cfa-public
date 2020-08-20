#!/usr/bin/env python
# coding: utf-8

# In[3]:


'''
Filename: Write URLs
Created July 2020
-----------------
For getting and writing Kenya Gazette URLs to provided filepath. 
Supports: 
- Connected Africa (use argument: connected_africa)
- Gazeti.Africa (use argument: gazeti)
-----------------
The URLs written are the final destination URLs, which point directly to
the gazette PDFs. 
-----------------
Please see the "Getting Data Walkthrough" file in the "additional documentation"
folder associated with step A (PDF to text) for more detailed explanation of
each of these outputs.
-----------------
Note that there is repeated code here; the functions for getting metadata were
written later in the development process. 
'''

import json
import requests
import os
import re
import csv


'''
Before downloading Gazeti files, you will need to download the URLs from
the Gazeti website, save them, and open the file wherever they are saved. 
Change this to reflect where you have saved the Gazeti files, and please
see the "Getting Data Walkthrough" for more details.
'''

gazeti_url_file = "/home/dssg-cfa/final_dest_urls/export.csv"

except_msg = "Please export gazette urls from gazeti.africa website.\n         Link to downloading Excel file for all Kenya Gazettes:\n         https://gazeti.africa/api/1/query/export?filter:collection_id=1\n         Convert to CSV, then upload as \'export.csv\'.\n         to /home/dssg-cfa/final_dest_urls/export.csv \n         Possible improvement: automate this"


# In[4]:


'''
1. Helpers for getting data from the Gazeti website. 
'''

def conn_afr_api_call():
    '''  
    This calls the Connected Africa API and returns metadata for all gazettes stored
    in the database. The metadata includes links, publication date, and other 
    identifying information. 
    '''
    headers = {
        'Accept': 'application/json',
        'Authorization': 'ApiKey c7ce69ddd9764dd095f8b2a3e157715f',
    }


    params = (
        ('facet', 'collection_id'),
        ('facet_size:collection_id', '10'),
        ('facet_total:collection_id', 'true'),
        ('filter:collection_id', '18'),
        ('filter:schema', 'Pages'),
        ('filter:schemata', 'Thing'),
        ('highlight', 'true'),
        ('limit', '10000'),
    )

    response = requests.get('https://data.connectedafrica.net/api/2/entities', headers=headers, params=params)

    data = response.text

    data_json = json.loads(data)
    
    return data_json



def get_img_urls_conn_af():
    '''
    Returns list of tuples with the format:
    tuple[0] = image url (which redirects to final destination URL)
    tuple[1] = year of publication
    These are from the Connected Africa website.
    Note that the "image URL" will not work with the Read API; the URL it redirects to
    is needed. 
    '''
    
    # Database #1: Connected Africa, accessed through API call
    print("Getting image redirect URLs from Connected Africa website...")
    
    data_json_ca = conn_afr_api_call()

    img_urls = []
    for result in data_json_ca['results']: 
        dated_str = result['properties']['publishedAt'][0]
        year = int(dated_str[:4])
        url = result['links']['file']
        
        if url in img_urls:
            print("duplicate")
            print(url)
        
        img_urls.append((url, year))

    print("Done.\n")
    return img_urls
        
                     
def get_ca_urls_metadata(yr_start = 0, yr_end = 7000): 
    '''
    Writes a JSON to filepath_out with gazette URLs from Connected Africa database
    and identifying information.
    
    For each gazette, this will look like a dictionary with the following keys: 
    - year: year of publication
    - fileNameDirectFromDB: filename, as it is written in the source database
    - dest_url: this is a temporary URL that points directly to the file. 
    - checksums: a hash of the content; unique for content
    - docid: the document ID; unique id for files in the database 
    - dest_url: a temporary URL (this will refresh every few days) pointing to the gazette PDF 
    
    '''
    
    data_json_ca = conn_afr_api_call()
    
    final_list = []
    count = 0
    print("Getting destination URLs and metadata...")
    
    for result in data_json_ca['results']:
        one_gazette = {}
        
        year = int(result['properties']['publishedAt'][0][:4])
        if year < yr_start or year > yr_end: 
            continue 
        
        one_gazette['year'] = year
        one_gazette['fileNameDirectFromDB'] = result['name']
        one_gazette['checksums'] = result['checksums']
        one_gazette['docid'] = result['id']
        url = result['links']['file']
        one_gazette['dest_url'] = requests.get(url, allow_redirects=False).headers['Location']
        
        final_list.append(one_gazette)
                
        count += 1
        if (count % 100 == 0 and count < 500) or (count % 500 == 0):
            print("Got info for " + str(count) + " gazettes")
        
    return final_list


# In[5]:


'''
2. Helper functions for getting data from Gazeti file. 
'''

def get_img_urls_gazeti():
    '''
    Returns dictionary with the format:
    tuple[0] = image url (which redirects to final destination URL)
    tuple[1] = year of publication
    These are from the gazeti.africa website
    '''

    print("Getting image redirect URLs from file " + gazeti_url_file + "...")
    if not os.path.exists(gazeti_url_file):
        raise Exception("Error: " + gazeti_url_file + " does not exist. \n" + except_msg)
  
    img_urls = []
    reader = csv.DictReader(open(gazeti_url_file, encoding='utf-8-sig')) 
    for line in reader:
        if line['File url'] in img_urls:
            print("duplicate")
            print(line['File url'])

        title = line['Title']
        year = int(title[-4:])
        img_urls.append((line['File url'], year))

    print("Done\n")
    return img_urls 


def get_gazeti_urls_metadata(yr_start = 0, yr_end = 7000):
    '''
    Writes a JSON to filepath_out with gazette URLs and identifying information
    about it and how it is stored in the source database. 
    
    For each gazette, this will look like a dictionary with the following keys:
    
    - year: year of publication
    - fileNameDirectFromDB: filename, as it is written in the source database
    - file_url: this is a permanent URL that redirects to the file. 
    it will be of the form: https://gazeti.africa/api/1/documents/[file_num]/file
    - dest_url: this is a temporary URL that points directly to the file. 
    - file_num: the unique number of the file in the Gazeti database. 
    '''
    
    if not os.path.exists(gazeti_url_file):
        raise Exception("Error: " + gazeti_url_file + " does not exist. \n" + except_msg)
  
    
    final_list = []
    count = 0
    reader = csv.DictReader(open(img_url_file, encoding='utf-8-sig')) 
    print("Getting destination URLs and metadata...")

    for line in reader:
        one_gazette = {}
        
        title = line['Title']
        year = int(title[-4:])
        if year < yr_start or year > yr_end: 
            continue 

        one_gazette['year'] = year
        one_gazette['fileNameDirectFromDB'] = line['File name'].replace('.pdf', '')
        url = line['File url']
        one_gazette['file_url'] = url
        file_num = re.search('documents/\d+', one_gazette['file_url']).group(0).replace("documents/", "")
        one_gazette['file_num'] = "num-" + file_num
        one_gazette['dest_url'] = requests.get(url, allow_redirects=False).headers['Location']
        
        final_list.append(one_gazette)
        
        count += 1
        if (count % 100 == 0 and count < 500) or (count % 500 == 0):
            print("Got info for " + str(count) + " gazettes")
    
    return final_list


# In[6]:


'''
3. General function to write destination URLs in bulk. 
'''

def write_dest_urls(source, filepath_out, metadata = False, yr_start = None, yr_end = None):
    '''    
    - Source: "connected_africa" or "gazeti"
    - filepath_out: the filepath wishing to save to
    - "metadata": specify whether to write out just the URLs or the 
    URLs and identifying metadata about documents. (default is False.)
    - yr_start & yr_end: if filtering for dates; inclusive
    '''
    
    # error checking: valid year range, valid filepath, valid source
    if yr_start and yr_end and yr_start > yr_end:
        raise Exception("Start year should be before end year.")
   
    f = open(filepath_out, 'w') 
    f.close()
    
    if source != "connected_africa" and source != "gazeti": 
        msg = "Invalid Source.\nPlease enter either \'connected_africa\' or \'gazeti\'"
        raise Exception(msg)
    
    # calls metadata functions, which filter by year and save JSONs to the file
    if metadata: 
        if source == "connected_africa": 
            final_list = get_ca_urls_metadata(yr_start, yr_end)
        elif source == "gazeti" and metadata:
            final_list = get_gazeti_urls_metadata(yr_start, yr_end)
        with open(filepath_out, 'w') as f: 
            json.dump(final_list, f)
        print("Done: " + str(count) + " urls saved to " + filepath_out)
        return

    
    # calls functions to just get URLs 
    if source == "connected_africa":
        img_urls = get_img_urls_conn_af()
    elif source == "gazeti":
        img_urls = get_img_urls_gazeti()
           
    if yr_start: 
        img_urls = list(filter(lambda t: t[1] >= yr_start, img_urls))
    if yr_end: 
        img_urls = list(filter(lambda t: t[1] <= yr_end, img_urls))
    
    img_urls = list(set([t[0] for t in img_urls]))
    
    final_dest_list = []
    count = 0
    
    print("Preparing to fetch " + str(len(img_urls)) + " final destination URLs\n")
    for url in img_urls: 
        final_dest_list.append(requests.get(url, allow_redirects=False).headers['Location'])
        count += 1
        if (count % 100 == 0 and count < 500) or (count % 500 == 0):
            print("Got " + str(count) + " final destination URLs")
    
    final_dest_list = list(set(final_dest_list))
    
    print("\nSuccess! Saving final destination URLs to " + filepath_out)
    print("Note that " + str(len(img_urls) - len(final_dest_list)) + " were duplicates")
    
    with open(filepath_out, 'w') as f:
        for url in final_dest_list:
            f.write('%s\n' % url)


# In[ ]:




