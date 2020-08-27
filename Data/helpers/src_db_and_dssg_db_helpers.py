#!/usr/bin/env python
# coding: utf-8

# In[22]:


import json

fn_map_file = "filename_map_to_database.txt"

with open(fn_map_file) as f:
    curr_fn_to_src = json.load(f)


# In[25]:


# initialize 

def add_elems(elem_lst, fn, dic):
    for elem in elem_lst: 
        if elem not in dic:
            dic[elem] = []
        dic[elem].append(fn)

def flip_dictionary(curr_fn_to_src):
    src_fn_to_curr, docidnum_map = {}, {}
    for gazette_name in curr_fn_to_src: 
        gazette_info = curr_fn_to_src[gazette_name]
        if 'src_database' not in gazette_info: # skip empty, failed gazettes
            continue
        add_elems(gazette_info['names_in_db'], gazette_name, src_fn_to_curr)
        if 'docids' in gazette_info: 
            add_elems(gazette_info['docids'], gazette_name, docidnum_map)
        if 'docnums' in gazette_info: 
            add_elems(gazette_info['docnums'], gazette_name, docidnum_map)
    return src_fn_to_curr, docidnum_map

src_fn_to_curr, docnum_map = flip_dictionary(curr_fn_to_src)


# In[26]:





# In[8]:


def get_names_in_src_db(curr_fn): 
    '''
    Given name in the DSSG database, return document names from the source database
    that correspond with the Gazette. 
    '''
    lst_ca = []
    lst_gaz = []
    for name in curr_fn_to_src[fn]['names_in_db']:
        if "gazette-ke-" in name: 
            lst_ca.append(name)
        if "opengazettes" in name: 
            lst_gaz.append(name)
    return {"connected-africa": lst_ca, "gazeti": lst_gaz}


# In[7]:


def get_ids_and_nums(curr_fn):
    '''
    Given name in the DSSG database, return document IDs and document numbers
    from the source databases that correspond with the Gazette.
    '''
    return [curr_fn_to_src[fn]['docids'], curr_fn_to_src[fn]['docnums']]


# In[32]:


def get_name_in_dssg_db(docNumOrId = None, srcDBName = None):
    '''
    Given a filename or document identifier from the *source* database 
    (Conn. Af. or Gazeti), return its corresponding filename in the DSSG-generated database. 
    '''
    if docNumOrId: 
        if docNumOrId not in docnum_map: 
            print("No corresponding file for this document number/id")
            return None
        return docnum_map[docNumOrId]
    if srcDBName:
        if srcDBName not in src_fn_to_curr: 
            print("No corresponding file for this document name")
            return None
        return src_fn_to_curr[srcDBName]

