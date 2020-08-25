#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
File: Check Gazette Filenames
------------------------------
Check that gazette filenames match the gazette file stored in the JSON.
Prints errors for manual checking. 
'''


import json
import os
from os import listdir, rename, path
import re

filepath = "/home/dssg-cfa/ke-gazettes/"


# In[ ]:


def is_special_issue(gazette_data):
    '''
    Returns if gazette is special issue (true) or not (false)
    '''
    
    first_page = gazette_data['analyzeResult']['readResults'][0]['lines']

    for line in first_page: 
        if 'SPECIAL ISSUE' in line['text']:
            return True
    
    return False


def get_date(gazette_data):
    '''
    Returns date reflected in gazette data
    '''
    
    first_page = gazette_data['analyzeResult']['readResults'][0]['lines']

    for line in first_page: 
        if 'NAIROBI' in line['text']:
            if not re.search(r', \d{4}', line['text']):
                continue
                        
            date = line['text'][9:]
            
            day = ""
            for ch in date[:2]:
                if ch.isdigit():
                    day += ch
            
            if len(day) == 1: 
                day = "0" + day
            
            month_start_idx = date.find(" ") + 1
            month_end_idx = date.find(",")
            month = date[month_start_idx:month_end_idx]
            
            year = date.strip()[-4:]
            
            return(("dated-" + day + "-" + month + "-" + year).strip().lower())
            
    
    return "" 


def is_dated_correctly(gazette_fn, gazette_data):
    '''
    Returns whether gazette is dated correctly
    If not dated correctly, returns correct date
    '''
    date = get_date(gazette_data)
    date_fn = re.search(r'dated-\d+-[a-z]+-\d{4}', gazette_fn).group()
    
    # filter for common bugs in getting date
    if (date != date_fn) and ("--" not in date) and (" " not in date) and (date[-4:].isdigit):
        return False, date 
        
    return True, ""


def is_numbered_correctly(gazette_fn, gazette_data, just_results = False):
    '''
    Returns false if vol or issue number from gazette_data are not correctly
    reflected in gazette_fn (filename)
    '''
    first_page = gazette_data['analyzeResult']['readResults'][0]['lines']

    txt = None
    for line in first_page: 
        if 'Vol' in line['text']: 
            txt = line['text']
            break
            
    if not txt:
        print("Unable to find string \'Vol\'; check manually")
        return False, ""
        
    idx_vol_start = txt.index("Vol") + 3
    
    if idx_vol_start > len(txt):
        print("\'Vol\' string and volume number are on different lines; check manually")
        return False, ""
    
    vol = re.search(r'[A-Z]+', txt[idx_vol_start:])
    
    if not vol: 
        print("Unable to find volume number; check manually")
        return False, ""
    
    vol = vol.group(0).lower()
    
    no = re.search("No", txt)
    if not no: 
        print("Unable to find string \'No\'; check manually")
        return False, ""
    
    no = re.search(r'\d+(A)?', txt[txt.index("No"):])
    if not no:  
        print("Unable to find issue number; check manually")
        return False, ""
    
    no = no.group(0).lower()
    
    if just_results: 
        return vol, no
    
    pre = 'gazette-ke-vol-' + vol + '-no-' + no + "-"
    
    # common bug -- 'h' is misread
    if pre in gazette_fn or (no in gazette_fn and "h" in vol): 
        return True, ""
    
    suffix = re.search("dated-\d+-[a-z]+-\d+(-special)?", gazette_fn).group(0)
    
    new_fn = pre + suffix
    
    return False, new_fn


# In[ ]:


def check_filename(gazette_fn, gazette_data):
    '''
    Parameters: current filename of gazette; data - json output from Read API
    Returns false if 
    - Incorrectly labelled as "special" 
    - Should be labelled as "special" and isn't
    - Dated incorrectly
    - Issue or volume number is incorrect
    
    Renames Gazettes.  
    Currently automatically renames Gazettes incorrectly labelled as -special / not special,
    because this is a common error and the detection for it is reliable. 
    Prompts user to rename the Gazette (Y/N options) if volume, issue, or date is incorrect.
    '''
    named_correctly = True
    
    print("**Checking " + gazette_fn + "**\n")
    
    # if there was an error getting the gazette, prompt to remove the file
    first_page = gazette_data['analyzeResult']['readResults'][0]['lines']
    if len(first_page) == 0:
        if ("Error" in gazette_data['analyzeResult']['readResults'][1]['lines'][0]['text']):
            print("Error almost definitely encountered")
            print("Empty first page and error message on second page.")
        else:
            print("Empty first page; likely error in gazette. Check in database.")
            
        confirm = input("Do you want to remove this file? (Y/N): ")
        if "Y" not in confirm and "y" not in confirm:
            print("Keeping file " + gazette_fn)
            return True
        else: 
            print("Removing file " + gazette_fn)
            os.remove(filepath + gazette_fn)
            print("Done.\n")
        return False
    
    # CHECK THAT FILENAME MATCHES GAZETTE CONTENT and prompt to rename
    if "-special" in gazette_fn and not is_special_issue(gazette_data):
        print("Gazette incorrectly labelled as special.")
        print("Calling \'rename_gazette\' with flag = \'from_special\'\n")
        renamed, new_fn = rename_gazette(gazette_fn, flag = "from_special")
        if renamed:
            gazette_fn = new_fn
        named_correctly = False
        
    if not "-special" in gazette_fn and is_special_issue(gazette_data):
        print("Gazette is a special issue and not labelled as such.")
        print("Calling \'rename_gazette\' with flag = \'to_special\'\n")
        renamed, new_fn = rename_gazette(gazette_fn, flag = "to_special")
        if renamed:
            gazette_fn = new_fn
        named_correctly = False
    
    date_correct, real_date = is_dated_correctly(gazette_fn, gazette_data)
    if not date_correct and len(real_date) > 0:
        print("Gazette is dated incorrectly.")
        print("Calling \'rename_gazette\' with flag = \'dated\' and dated_str = " + real_date + "\n")
        renamed, new_fn = rename_gazette(gazette_fn, flag = "dated", dated_str = real_date)
        if renamed:
            gazette_fn = new_fn
        named_correctly = False
        
    number_correct, new_fn = is_numbered_correctly(gazette_fn, gazette_data)
    if not number_correct and len(new_fn) > 0:
        print("Gazette volume/issue numbering is incorrect.")
        print("Calling \'rename_gazette\' with flag \'pre\' and fn_with_pre = " + new_fn + "\n")
        renamed, new_fn = rename_gazette(gazette_fn, flag = "pre", fn_with_pre = new_fn)
        if renamed:
            gazette_fn = new_fn
        named_correctly = False
    
    print("-------------")
    return named_correctly


# In[ ]:


def rename_gazette(gazette_fn, flag, dated_str = "", fn_with_pre = ""):
    '''
    ONLY CALL THIS FUNCTION IF YOU ARE SURE YOU WANT TO RENAME SOMETHING 
    Rename gazette at gazette_fn according to flag: 
        to_special: add "-special" at end
        from_special: remove "-special" from end
        dated: change the date in the file name to `dated`
        pre: change issue/volume number prefix
    '''
    
    if flag == "to_special": 
        new_fn = gazette_fn.strip() + "-special"
    
    elif flag == "from_special":
        new_fn = gazette_fn.strip()[0:-8]
    
    # a bit more complicated --
    # need to ensure preservation of '-special' & of vol/issue numbers, if applicable
    elif flag == "dated": 
        new_fn = dated_str
        if "-special" in gazette_fn:
            new_fn += "-special"
        pre = re.search(r'gazette-ke-vol-[a-zA-Z]+-no-\d{1,4}(a)?-', gazette_fn).group(0)
        if pre: 
            new_fn = pre + new_fn
    
    elif flag == "pre": 
        new_fn = fn_with_pre
        
    else: 
        raise Exception("Invalid flag arg: should be to_special, from_special, dated, or pre")
    
    if path.exists(filepath + new_fn):
        print("Error: gazette already exists. Not renaming.")
        print("New filename (attempted): " + new_fn)
        print("Current filename: " + gazette_fn + "\n")
        # Recommend uncommenting this only once all files are correctly named 
        # os.remove(filepath + gazette_fn)
        return False, ""
    
    print("Renaming " + gazette_fn + " to " + new_fn)
    
    # Prompt user to confirm before changing date or volume/issue numbering
    # The to/from special code is quite accurate, but *change this if you have concerns.*
    if "special" in flag: 
        confirm = "Y"
    else: 
        confirm = input("Are you sure you want to rename? (Y/N): ")
    if "Y" not in confirm and "y" not in confirm:
        print("Not renaming file " + gazette_fn + " to " + new_fn + ".\nStopping...\n")
        return False, ""
    
    rename(filepath + gazette_fn, filepath + new_fn)
    print("Done.\n")
    return True, new_fn


# In[ ]:


def check_all_filenames(yr_start = 0, yr_end = 0):
    '''
    Check all filenames against gazette data. 
    Option to filter by year. 
    
    Calls `rename_gazette`, which prompts user to rename if they would like to. (Y/N)
    NOTE: Currently `check_filename` is implemented to auto-rename Gazettes that are
    incorrectly labelled as special / not special issues. 
    Change this in `rename_gazette` if you have concerns. 
    '''
    if (yr_start == 0 and yr_end > 0) or (yr_start > 0 and yr_end == 0):
        print("Error: must enter both yr_start and yr_end")
        return
    
    
    # path where gazettes are stored
    path = "/home/dssg-cfa/ke-gazettes/"
    
    fn_list = [f for f in listdir(path)]
    
    # filter by year 
    if yr_start > 0:  
        yr_list = [str(y) for y in range(yr_start, yr_end)]
        fn_list = list(filter(lambda f: re.search(r'\d{4}', f).group(0) in yr_list, fn_list))
    
    for gazette_fn in fn_list: 
        with open(path + gazette_fn) as f: 
            gazette_data = json.load(f)
        
        check_filename(gazette_fn, gazette_data)

