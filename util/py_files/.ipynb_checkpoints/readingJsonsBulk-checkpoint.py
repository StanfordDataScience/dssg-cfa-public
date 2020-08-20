#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -----------------------------------------------------------
# Bulk converting Thea's jsons into T's segments.
# 
# Written primarily by Robbie thus far.
# -----------------------------------------------------------


# In[3]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "pdf_to_text/Post-Processing/py_files"
GAZETTESDIR = "/home/dssg-cfa/ke-gazettes"
EXPORTDATADIR1 = ROUTETOROOTDIR + 'NER/csv_outputs'
EXPORTDATADIR2 = ROUTETOROOTDIR + 'NER/csv_outputs_include_early'
import os
import json

os.chdir(IMPORTSCRIPTSDIR)
import retoolingSegmentation
import orderingText
import setup


# In[3]:


def getListOfJsons(filepath = GAZETTESDIR):
    """Get a list of all the filenames of all gazettes in our database.
    
    args:
    filepath: filepath to the directory to search for gazette jsons in.
    
    returns: a list of all the filenames of all gazettes in our database"""
    
    os.chdir(GAZETTESDIR)
    ret = get_ipython().getoutput('ls')
    return ret

# load filenames into a list for future use
listOfJsons = getListOfJsons()
os.chdir(IMPORTSCRIPTSDIR)

def readJsonIntoDict(jsonNum, pageNum = 'all'):
    """Read a json from Read API into a Python dictionary and return it.
    
    args:
    jsonNum: The index of the gazette json by alphabetical order to convert and return.
    pageNum: The page number of the gazette to return in dictionary format.
        If pageNum == 'all', then return all pages.
        
    returns: A highly nested Python dictionary from Read API's json output.
    To understand the structure of this dictionary better, see Microsoft's help pages."""
    
    os.chdir(GAZETTESDIR)
    filename = listOfJsons[jsonNum]
    with open(filename) as json_file:
        data = json.load(json_file)
    pages_list = data['analyzeResult']['readResults']
    if pageNum == 'all':
        return pages_list
    else:
        return pages_list[pageNum]['lines']
    
def getLines(jsonDict, pageNum):
    """Given a dictionary from Read API which contains all pages and a page number, 
    return the lines from that page num in Python dictionary format.
    
    args:
    jsonDict: a Python dictionary from a call to Read API of a complete gazette.
    pageNum: the page whose lines will be returned.
    
    returns: A highly nested Python dictionary from Read API's json output.
    To understand the structure of this dictionary better, see Microsoft's help pages."""
    
    return jsonDict[pageNum]['lines']

def getNumPages(jsonDict):
    """Given a dictionary from Read API, return the number of pages it has.
    
    args:
    jsonDict: a Python dictionary from a call to Read API of a complete gazette.
    
    returns: the number of pages in the (json of the) gazette."""
    
    numPages = 0
    working = True
    while working:
        try:
            useless = jsonDict[numPages]['lines']
            numPages += 1
        except:
            working = False
    return numPages


# In[4]:


def readPage(jsonDict, pageNum, keepPageHeader = False, includeTables = False, cleaningFns = []):
    """Given a json dict of a gazette, read the text of a page into one string and return it.
    
    args:
    jsonDict: dictionary representing an entire gazette
    pageNum: page number to read
    keepPageHeader: If True keep the three items appearing at the top of each page 
            (date, "The Kenya Gazette", page num)
    includeTables: if True, include the transcription of pages which look like tables (>2 columns).
         Otherwise, return the empty string for table pages.
    cleaningFNs: functions to call on the text to clean it up (ie replacing 'No.' with 'number')
    
    returns: the cleaned and ordered text of one gazette page."""
    
    page_lines = getLines(jsonDict, pageNum)
    if len(page_lines) < 20:
        # not enough lines on this page, don't bother with it.
        return ''
    if pageNum == 0:
        text = orderingText.readTitlePage(page_lines)
    else:
        numCols = orderingText.getNumCols(page_lines)
        if numCols == None or numCols > 2:
            if includeTables:
                text = orderingText.readTablePage(page_lines)
            else:
                return ''
        else:
            text = orderingText.read2ColPagePreserveParagraphs(page_lines)
    for fn in cleaningFns:
        text = fn(text)
    return text

def readEntireGazette(jsonNum, keepPageHeader = False, includeTables = False, cleaningFns = []):
    """Read the text of an entire gazette into one string and return it (in order).
    
    args:
    jsonNum: json index number of the gazette to read (in jsonList).
    keepPageHeader: If True keep the three items appearing at the top of each page 
            (date, "The Kenya Gazette", page num).
    includeTables: if True, include the transcription of pages which look like tables (>2 columns).
         Otherwise, return the empty string for table pages.
    cleaningFNs: functions to call on the text to clean it up (ie replacing 'No.' with 'number').
    
    returns: the cleaned and ordered text of one gazette."""
    
    jsonDict = readJsonIntoDict(jsonNum)
    numPages = getNumPages(jsonDict)
    ret = ''
    for pageNum in range(0, numPages):
        ret += readPage(jsonDict, pageNum, keepPageHeader, includeTables, cleaningFns)
    return ret

def writeEntireGazetteToCsv(jsonNum, filepath = 'default',
                       filename = 'default', keepPageHeader = False, includeTables = False, 
                       cleaningFns = [], includeSpecial = False, includeNonLRA = False,
                       startYear = 2017, endYear = 2020):
    """Write into csv format an entire gazette. Extract named entities using regexes.
    Write only certain segments to csv format.
    
    args:
    jsonNum: json index number of the gazette to read (in jsonList).
    filepath: filepath to write the csv to.
    filename: file name to write the csv to.
    keepPageHeader: If True keep the three items appearing at the top of each page 
            (date, "The Kenya Gazette", page num)
    includeTables: if True, include the transcription of pages which look like tables (>2 columns).
         Otherwise, return the empty string for table pages.
    cleaningFNs: functions to call on the text to clean it up (ie replacing 'No.' with 'number').
    includeSpecial: If False, do not write a csv for a gazette whose title includese the word 'special'.
    includeNonLRA: If True, include all land-related seg
    startYear, endYear: If the gazette was published within this range of years (inclusive), 
        write it to csv. Otherwise, do not.
    
    returns: a pandas dataframe with regex-extracted entities by segment. 
        Will return 0 if no segments are found. Includes only segments that are land-related
        if includeNonLRA is true, and only segments with the header 'THELAND REGISTRATION ACT' 
        if includeNonLRA is false. """
    
    if filepath == 'default':
        filepath = EXPORTDATADIR1
    if filename == 'default':
        filename = 'entities_' + listOfJsons[jsonNum]
        
    if 'special' in filename and not includeSpecial:
        return
    
    goodYear = False
    for year in range(startYear, endYear + 1):
        if str(year) in filename:
            goodYear = True
            break
            
    if not goodYear:
        return
        
    text = readEntireGazette(jsonNum, keepPageHeader, includeTables, cleaningFns)
    return retoolingSegmentation.writeEntitiesToCsv(text, filename, filepath, includeNonLRA = includeNonLRA)


# In[5]:


def writeGroupOfGazettesToCsv(startI, endI, filepath = 'default',
                         filename = 'default', keepPageHeader = False, includeTables = False, 
                         cleaningFns = [], includeSpecial = False, includeNonLRA = False,
                         startYear = 2017, endYear = 2020):
    """Write into csv format a range of gazettes. Extract named entities using regexes.
    Write only certain segments to csv format, and only from certain gazettes.
    
    args:
    startI, endI: attempt to write to csvs gazettes from this range of indices in jsonList.
        Include startI, do not include endI.
    filepath: filepath to write the csv to.
    filename: file name to write the csv to.
    keepPageHeader: If True keep the three items appearing at the top of each page 
            (date, "The Kenya Gazette", page num)
    includeTables: if True, include the transcription of pages which look like tables (>2 columns).
         Otherwise, return the empty string for table pages.
    cleaningFNs: functions to call on the text to clean it up (ie replacing 'No.' with 'number').
    includeSpecial: If False, do not write a csv for a gazette whose title includese the word 'special'.
    includeNonLRA: If True, include all land-related seg
    startYear, endYear: If the gazette was published within this range of years (inclusive), 
        write it to csv. Otherwise, do not. """
    
    for i in range(startI, endI):
        writeEntireGazetteToCsv(i, filepath, filename, startYear = startYear, endYear = endYear, 
                                includeNonLRA = includeNonLRA, includeSpecial = includeSpecial,
                                keepPageHeader = keepPageHeader, includeTables = includeTables,
                                cleaningFns = cleaningFNs)
        


# In[6]:


def findGazetteNumByName(searchName):
    """Find the indices of gazettes whose names contain the string given in searchName
    from the global variable listOfJsons.
    
    args: 
    searchname: (partial) name to search for in jsonList.
    
    returns: a list of indices which match the search query."""
    
    ret = []
    for i in range(len(listOfJsons)):
        jsonName = listOfJsons[i]
        if searchName in jsonName:
            ret.append(i)
    return ret


# In[7]:


def writeTrainSet():
    """Write to csv all gazettes that we will use to train out spaCy model.
    This train set is gazettes between 2017 and 2020, only including land registration
    act segments."""
    
    writeGroupOfGazettesToCsv(0, len(listOfJsons), startYear = 2017, endYear = 2020, 
                              includeNonLRA = False, filepath = EXPORTDATADIR1)
    
def writeAllGazettes():
    """Write to csv all gazettes from 2012 to 2020. Inlcude all land-related segments."""
    
    writeGroupOfGazettesToCsv(0, len(listOfJsons), startYear = 2012, endYear = 2020, 
                              includeNonLRA = True, filepath = EXPORTDATADIR2)


# In[8]:




