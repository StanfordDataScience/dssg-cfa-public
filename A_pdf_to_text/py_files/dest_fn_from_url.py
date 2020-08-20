#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
File: Gazette Destination Filename from Final Destination URL
Created July 2020
--------------------
Gets gazette names from final destination URLs 
Renames gazettes into our consistent naming schema, which is: 
- use "-", not "_" between words
- gazette issue number is numerical (e.g., "9")
- gazette volume number is roman numeral
- prefix is: "gazette-ke-"
- all lowercase
- if applicable, the "special" flag is at the end of the title
'''

import re


# In[ ]:


# HELPERS

num_dict = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000,'IV':4,'IX':9,'XL':40,'XC':90,'CD':400,'CM':900}

def roman2num(roman): 
    '''
    Roman numeral to number. 
    '''
    num = 0
    i = 0
    while i < len(roman): 
        if i+1 < len(roman) and roman[i:i+2] in num_dict: 
            num += num_dict[roman[i:i+2]]
            i += 2
        else: 
            num += num_dict[roman[i]]
            i+=1
    return num


num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
           (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]

def num2roman(num):
    '''
    Number to roman numeral.
    '''
    roman = ''

    while num > 0:
        for i, r in num_map:
            while num >= i:
                roman += r
                num -= i

    return roman


# In[ ]:


def get_name_gazet_orig(final_dest_url):
    '''
    Get name from final dest URL & return it in *Gazeti's original naming schema*
    '''
    return re.search('ke-vol-\d+-no-\d{1,4}(a)?(-special)?-dated-\d{1,2}-[a-zA-Z]+-\d{4}', final_dest_url).group(0)


def get_name_gazeti(final_dest_url): 
    '''
    Get name from final dest URL & return it within our naming schema. 
    '''
    s = get_name_gazet_orig(final_dest_url)
    s = "gazette-" + s
    
    vol = (re.findall(r'vol-\d+', s)[0])
    
    vol_roman = "vol-" + num2roman(int(vol[4:]))
    
    s = s.replace(str(vol), vol_roman)
    
    if "-special" in s:
        s = s.replace("-special", "")
        s += "-special"
    
    return s.lower()


def get_name_conn_af(final_dest_url):
    '''
    Get name from final dest URL & return it within our naming schema. 
    '''
    s = re.search(r'gazette_ke_vol_[a-zA-Z]+_no_\d{1,4}_dated_\d{1,2}_[a-zA-Z]+_\d{4}(_special)?', final_dest_url).group(0)
    s = s.replace("_", "-")
    return s.lower()


# In[ ]:


def get_name(final_dest_url, flag = None):
    '''
    Flag = optional argument regarding source of URL (gazeti or Connected Africa)
    If not provided, get_name will determine source based on URL patterns
    '''
    
    if not flag: 
        if "cfa-opengazettes" in final_dest_url:
            flag = "gazeti"
        elif "ancir-aleph" in final_dest_url:
            flag = "connected_africa"
        else:
            raise Exception("Cannot determine source for\n" + final_dest_url)
    
    if flag == "gazeti":
        return get_name_gazeti(final_dest_url)
    elif flag == "connected_africa":
        return get_name_conn_af(final_dest_url)
    else: 
        raise Exception("Invalid flag argument; please pass gazeti or connected_africa")


# In[ ]:


def to_gazeti_format(name): 
    '''
    Given name in our standard format, described in header comment of this file. 
    Returns version of name that's searchable on the gazeti.africa website
    '''
    vol = (re.findall(r'vol-[A-Z]+', name)[0]).replace("vol-", "")
    vol_num = roman2num(vol)
    name = name.replace(vol, str(vol_num))
    
    if "special" in name:
        name = name.replace("-special", "")
        idx = name.index("-dated")
        name = name[:idx] + "-special" + name[idx:]
    
    return name

