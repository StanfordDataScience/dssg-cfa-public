#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
import requests 
import os

from helpers import check_gazette_filenames as cf 
from helpers import write_urls as wu
from helpers import dest_fn_from_url as df

FOLDER = "/home/dssg-cfa/ke-gazettes-first-pgs/"
FOLDER_CURR = "/home/dssg-cfa/ke-gazettes/"


# In[ ]:


'''
The final data structure will have the form: 
- Key: name in our database
- Value: a dictionary with
--- src_database: source database(s) (list)
--- names_in_db (list)
--- checksums: (if connected africa) -- a list, but should just be one of these
--- docids: (if connected africa) document id (unique to the document) 
--- docnums: (if gazeti) document number 
'''


# In[ ]:


# create a mapping from hash (checksums) and name to doc ID 
def get_to_id(): 
    data_json = wu.conn_afr_api_call()
    hash_and_name_to_id = {}

    for result in data_json['results']: 
        checksums = result['checksums'][0]
        name = result['name']
        if (checksums, name) not in hash_and_name_to_id:
            hash_and_name_to_id[(checksums, name)] = []
        hash_and_name_to_id[(checksums, name)].append(result['id'])
    
    return hash_and_name_to_id

def info_to_std_format(vol, issue, date, special): 
    if vol.isdigit():
        vol = df.num2roman(int(vol))
    name = "gazette-ke-vol-" + vol.lower() + "-no-" + issue + "-" + date
    if special:
        name += "-special"
    return name.lower()


def fn_to_std_format(fn):
    checksum = fn[fn.rfind("_") + 1:].replace("*", "")
    special = "special" in fn
    fn_trimmed = fn.replace("-special", "")
    vol = fn_trimmed[fn_trimmed.find("vol-") + 4:fn_trimmed.find("-no")]
    no = fn_trimmed[fn_trimmed.find("no-") + 3:fn_trimmed.find("-dated")]
    dated = fn_trimmed[fn_trimmed.find("dated-"):fn_trimmed.find("_")]
    return info_to_std_format(vol, no, dated, special)


def get_true_fn(gazette_data): 
    vol, issue = cf.is_numbered_correctly("", gazette_data, just_results = True)
    if not vol or not issue:
        return "invalid_fn_placeholder"
    date = cf.get_date(gazette_data)
    special = cf.is_special_issue(gazette_data)
    return info_to_std_format(vol, issue, date, special)


def get_info_gazeti(fn, new_fn, gazette_data, fn_mapping): 
    '''
    Given: filepath to first page JSON
    Returns: 
    (1) new filename (directly from Gazette, in our format)
    (2) dictionary with appropriate information
    '''
    fn = fn.replace(FOLDER, "")
    if new_fn in fn_mapping: 
        to_src = fn_mapping[new_fn]
        if "docnums" not in to_src:
            to_src["docnums"] = []
    else: 
        to_src = {"src_database": [], "names_in_db": [], "docnums": []}
    
    if "gazeti" not in to_src["src_database"]:
        to_src["src_database"].append("gazeti")
    
    src_name = fn[0:fn.find("_")]
    if src_name not in to_src["names_in_db"]:
        to_src["names_in_db"].append(src_name)
        
    num = fn[fn.rfind("-") + 1:]
    to_src["docnums"].append(num)
    
    return to_src

    
def get_info_conn_af(fn, new_fn, gazette_data, fn_mapping, hash_and_name_to_id): 
    '''
    Given: filepath to first page JSON
    Returns: 
    (1) new filename (directly from Gazette, in our format)
    (2) dictionary with appropriate information
    '''
    fn = fn.replace(FOLDER, "")
    if new_fn in fn_mapping: 
        to_src = fn_mapping[new_fn]
        if "checksums" not in to_src: 
            to_src["checksums"] = []
            to_src["docids"] = []
    else: 
        to_src = {"src_database": [], "names_in_db": [], "checksums": [], "docids": []}
    
    if "connected-africa" not in to_src["src_database"]:
        to_src["src_database"].append("connected-africa")
    
    src_name = fn[0:fn.find("_")]
    if src_name not in to_src["names_in_db"]:
        to_src["names_in_db"].append(src_name)
    
    checksum = fn[fn.rfind("_") + 1:].replace("*", "")
    if checksum not in to_src["checksums"]:
        to_src["checksums"].append(checksum)
    
    id_list = hash_and_name_to_id[(checksum, src_name)]
    for docid in id_list:
        if docid not in to_src['docids']:
            to_src['docids'].append(docid)
    
    return to_src

def get_info():
    fn_mapping = {}
    fn_mapping["empty_files"] = []
    failures = []
    hash_and_name_to_id = get_to_id()
    fns = [f for f in os.listdir(FOLDER)]
    fns = [FOLDER + f for f in fns]
    curr_fns = [f for f in os.listdir(FOLDER_CURR)]
    
    count = 0
    
    for fn in fns: 
        with open(fn) as f: 
            gazette_data = json.load(f)
        
        first_page = gazette_data['analyzeResult']['readResults'][0]['lines']
        if len(first_page) == 0:
            fn_mapping["empty_files"].append(fn.replace(FOLDER, ""))
            continue
        
        new_fn = get_true_fn(gazette_data)
        
        if new_fn not in curr_fns:
            failures.append(fn.replace(FOLDER, ""))
            continue
            
        if "connected-africa" in fn: 
            to_src = get_info_conn_af(fn, new_fn, gazette_data, fn_mapping, hash_and_name_to_id)
        elif "gazeti" in fn: 
            to_src = get_info_gazeti(fn, new_fn, gazette_data, fn_mapping)
        else:
            print("invalid filename for " + fn + "\n")
            continue
            
        fn_mapping[new_fn] = to_src
 
    failures = loop_failures(failures, fn_mapping, curr_fns, hash_and_name_to_id)
    fn_mapping['failed_to_map_from_cfa_db'] = failures
    
    print("failed on " + str(len(failures)))
    return fn_mapping


def loop_failures(failures, fn_mapping, curr_fns, hash_and_name_to_id):
    
    new_failed = {}
    
    for fn in failures:
        new_fn = fn_to_std_format(fn)
        
        with open(FOLDER + fn) as f:
            gazette_data = json.load(f)
         
        if cf.is_special_issue(gazette_data): 
            if "-special" not in new_fn: 
                new_fn += "-special" 
        else: 
            if "-special" in new_fn:
                new_fn = new_fn.replace("-special", "")
        
        if new_fn in curr_fns:  
            if "connected-africa" in fn: 
                to_src = get_info_conn_af(fn, new_fn, gazette_data, fn_mapping, hash_and_name_to_id) 
            elif "gazeti" in fn:
                to_src = get_info_gazeti(fn, new_fn, gazette_data, fn_mapping)
            fn_mapping[new_fn] = to_src
        else:
            new_failed[fn] = new_fn
    
    return new_failed

