#!/usr/bin/env python
# coding: utf-8

# In[2]:


# -----------------------------------------------------------
# Create training data for our SpaCy model in the form specified in the below chunks.
# 
# Written primarily by Robbie thus far.
# -----------------------------------------------------------


# In[3]:


# TRAIN_DATA_3 = [
#     (sample_gazette_1, {
#         'entities': 
#         [(12, 35, 'OWNER'), (44, 68, 'OWNER 2'), (78, 98, 'OWNER ADDRESS'), (151, 176, 'OWNERSHIP'), (230, 259, 'LAND SIZE'), (325, 349, 'LAND TITLE'), (457, 461, 'DEED STATUS')]
#     }),
#     (sample_gazette_1, {"entities": ents_1}),
#     (sample_gazette_2, {"entities":
#     [(8, 28, 'OWNER'), (33, 47, 'OWNER ADDRESS'), (110, 125, 'OWNERSHIP'), (179, 208, 'LAND SIZE'), (274, 302, 'LAND TITLE'), (410, 414, 'DEED STATUS')]                   
#     }),
#     (sample_gazette_2, {"entities": ents_2}),

#     (sample_gazette_3, {'entities': [(8, 27, 'OWNER'), (32, 52, 'OWNER ADDRESS'), (105, 130, 'OWNERSHIP'), (184, 212, 'LAND SIZE'), (278, 312, 'LAND TITLE'), (420, 424, 'DEED STATUS')]    
#                        }),
    
#     (sample_gazette_3, {"entities": ents_3}),
#     (sample_gazette_4, {"entities": [(12, 35, 'OWNER'), (44, 66, 'OWNER 2'), (76, 96, 'OWNER ADDRESS'), (149, 181, 'OWNERSHIP'), (228, 255, 'LAND SIZE'), (321, 346, 'LAND TITLE'), (454, 458, 'DEED STATUS')]
#                        }),
#     (sample_gazette_4, {"entities": ents_4}),
    
# ]


# Format: 
# List, with one entry for each text in the train set. Each item in the list is a tuple with
# 
#     1) the text itself
#     
#     2) a dictionary with one entry
#     
#         key: only one, always just the string 'entities'
#         
#         value: a list, with one item for each flagged entity. Each item is a thruple with
#         
#             1) start index of entity within text
#             
#             2) end index of entity within text
#             
#             3) categorization of said entity (i.e. 'PERSON')
#             
# Later in this document, when we mention "the tuple required for spaCy training data, we are referring to the three-tuple at the bottom of this list: 
# 
# (start index of entity within text, end index of entity within text, categorization of said entity (i.e. 'PERSON')).

# In[4]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
UTILDIR = ROUTETOROOTDIR + 'util'
JSONSDIR = ROUTETOROOTDIR + 'A_pdf_to_text/jsons_ke_gazettes/'
CSVTRAINDIR = ROUTETOROOTDIR + 'B_text_preprocessing/csv_outputs_train/'
CSVTESTDIR = ROUTETOROOTDIR + 'B_text_preprocessing/csv_outputs_test/'
import os            
import json
import pandas as pd
import numpy as np
import re

os.chdir(IMPORTSCRIPTSDIR)
import retoolingSegmentation
import orderingText
import setup
import readingJsonsBulk


# In[5]:


def getListOfCsvs(filepath):
    """Get a list of all filenames of entity-containing csvs.
    
    args:
    filepath: the filepath to the directory to search.
    
    returns: a list of all filenames in said directory."""
    
    os.chdir(filepath)
    ret = get_ipython().getoutput('ls')
    return ret

# load all filenames into global variables
listOfCsvsNew = getListOfCsvs(CSVTRAINDIR)    # this is generally our training and validation sets
listOfCsvsOld = getListOfCsvs(CSVTESTDIR)    # this is generally our test set (non-LRA segments)


# In[26]:


def readProcessedGazette(gazetteNum, newOnly = True):
    """Read the csv of a processed gazette into a Pandas dataframe.
    
    args:
    gazetteNum: the index of the csv to pull.
    newOnly: If True, pull from the csvs in CSVTRAINDIR (new) (train set) (LRA only).
        Otherwise, pull from the csvs in CSVTESTDIR (new and old) (test set) (all land segs).
        
    returns: a pandas dataframe representing a pre-processed gazette."""
    
    if newOnly:
        os.chdir(CSVTRAINDIR)
        df = pd.read_csv(listOfCsvsNew[gazetteNum])
    else:
        os.chdir(CSVTESTDIR)
        df = pd.read_csv(listOfCsvsOld[gazetteNum])
    return df

def getColAsSeries(df, colString):
    """Given a pandas dataframe and a string representing the name of a column, return that column as a series."""
    
    return df[[colString]][colString]

def getMaskOfGoodCols(df):
    """Return an np array of booleans, with true for each entry in our pandas df that we want to process.
    We only want to process rows with inner text of length at least 100.
    
    args: 
    df: pandas df representing one regex-extracted entites csv.
    
    returns: a mask representing rows we wish to process."""
    
    textArr = getColAsSeries(df, 'inner text')
    longEnough = np.array([len(str(text)) > 100 for text in textArr])

    return longEnough


# In[27]:


# list of strings which are typically found in company names.
COMPANY_STRS = ['Limited', 'Liability', 'Company', 'LLC', 'Ltd', 'Partnership', 'PLP', 'Incorporated', 'Inc'
                       'Public', 'PLC', 'Corporation', 'Company', 'Foundation', 'Comission', 'Bank', 'Group']

def checkCompany(text):
    """Check to see if a string looks like it is the name of a company.
    
    args: 
    text: the string to check for company-ness.
    
    returns: True if text contains any of the strings found in COMPANY_STRS (global),
        False otherwise."""
    
    for string in COMPANY_STRS:
        if string in text:
            return True
    return False

def getOwnerTuple(series):
    """Get the three-tuple required for spaCy training data for OWNER.
    Extracts the owner using our preprocessing csv.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    resulting_names = []
    
    namestr = series['name']
    innerText = series['inner text']
    if type(namestr) == float:
        #no name
        return []
    if innerText.find('(4)') != -1:
        return fourNames(series)
    if innerText.find('(3)') != -1:
        return threeNames(series)
    if innerText.find('(2)') != -1:
        return twoNames(series)
    start = innerText.find(namestr)
    
    if checkCompany(namestr):
        resulting_names.append((start, start + len(namestr), 'ORG'))
    else:
        resulting_names.append((start, start + len(namestr), 'PERSON'))
    
    return resulting_names


def fourNames(series):
    """Helper method for getOwnerTuple(). Helps to extract names when there are four names in the entry.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    resulting_names = []
    
    innerText = series['inner text']
    names = re.search(r"\(1\) (.*?), \(2\) (.*?), \(3\) (.*?) and \(4\) (.*?),", innerText)
    try:
        name1 = names[1]
        name2 = names[2]
        name3 = names[3]
        name4 = names[4]
        start1 = innerText.find(name1)
        start2 = innerText.find(name2)
        start3 = innerText.find(name3)
        start4 = innerText.find(name4)
        
        if checkCompany(name1):
            resulting_names.append((start1, start1 + len(name1), 'ORG'))
        else:
            resulting_names.append((start1, start1 + len(name1), 'PERSON'))
        
        if checkCompany(name2):
            resulting_names.append((start2, start2 + len(name2), 'ORG'))
        else:
            resulting_names.append((start2, start2 + len(name2), 'PERSON'))
            
        if checkCompany(name3):
            resulting_names.append((start3, start3 + len(name3), 'ORG'))
        else:
            resulting_names.append((start3, start3 + len(name3), 'PERSON'))
            
        if checkCompany(name4):
            resulting_names.append((start4, start4 + len(name4), 'ORG'))
        else:
            resulting_names.append((start4, start4 + len(name4), 'PERSON'))
            
        return resulting_names
    
    
    except:
        return []

def threeNames(series):
    """Helper method for getOwnerTuple(). Helps to extract names when there are three names in the entry.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    resulting_names = []
    
    innerText = series['inner text']
    names = re.search(r"\(1\) (.*?), \(2\) (.*?) and \(3\) (.*?),", innerText)
    try:
        name1 = names[1]
        name2 = names[2]
        name3 = names[3]
        
        start1 = innerText.find(name1)
        start2 = innerText.find(name2)
        start3 = innerText.find(name3)
        
        if checkCompany(name1):
            resulting_names.append((start1, start1 + len(name1), 'ORG'))
        else:
            resulting_names.append((start1, start1 + len(name1), 'PERSON'))
        
        if checkCompany(name2):
            resulting_names.append((start2, start2 + len(name2), 'ORG'))
        else:
            resulting_names.append((start2, start2 + len(name2), 'PERSON'))
            
        if checkCompany(name3):
            resulting_names.append((start3, start3 + len(name3), 'ORG'))
        else:
            resulting_names.append((start3, start3 + len(name3), 'PERSON'))
            
        return resulting_names

    except:
        return []
    

def twoNames(series):
    """Helper method for getOwnerTuple(). Helps to extract names when there are two names in the entry.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    resulting_names = []
    
    innerText = series['inner text']
    names = re.search(r"\(1\) (.*?) and \(2\) (.*?),", innerText)
    try:
        name1 = names[1]
        name2 = names[2]
        start1 = innerText.find(name1)
        start2 = innerText.find(name2)
        
        if checkCompany(name1):
            resulting_names.append((start1, start1 + len(name1), 'ORG'))
        else:
            resulting_names.append((start1, start1 + len(name1), 'PERSON'))
        
        if checkCompany(name2):
            resulting_names.append((start2, start2 + len(name2), 'ORG'))
        else:
            resulting_names.append((start2, start2 + len(name2), 'PERSON'))
            
        return resulting_names
    except:
        return []



def getOwnerAddressTuple(series):
    """Get the tuple required for spaCy training data for OWNER ADDRESS.
    Extracts the address using our preprocessing csv.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    address = series['address']
    if type(address) == float or len(address) < 5:          #5 is a magic number
        return []
    innerText = series['inner text']
    start = innerText.find(address)
    return [(start, start + len(address), 'OWNER ADDRESS')]

def getTupleTag(series, colname, tagname):
    """Get the tuple required for spaCy training data for any variety of columns in preprocessing.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    colname: name of column in pre-processed csv to pull from
    tagname: name to tag entities to.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    text = series[colname]
    if type(text) != str and np.isnan(text):
        return []
    text = orderingText.convertNoToNumbers(str(text))
    innerText = series['inner text']
    start = innerText.find(text)
    return [(start, start + len(str(text)), tagname)]

def getDeedStatus(innerText):
    """Gets the status of the deed in the text in question. 
    Returns information in tuple required for spaCy training.
    
    args:
    innerText: the text of a gazette segment, minus headers and footers.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    ret = []
    if 'lost' in innerText:
        start = innerText.find('lost')
        ret.append((start, start + 4, 'DEED STATUS'))
    if 'cancelled and of no effect' in innerText:
        start = innerText.find('cancelled and of no effect')
        ret.append((start, start + 26, 'DEED STATUS'))
    return ret

def getOwnershipStatus(innerText):
    """Gets the status of ownership in the text in question. 
    Returns information in tuple required for spaCy training.
    
    args:
    innerText: the text of a gazette segment, minus headers and footers.
    
    returns: a list of three-tuples required for spaCy training data (could be empty)."""
    
    ret = []
    strsToFind = ["proprietor in absolute ownership", "proprietors in absolute ownership",
                  "proprietor lessee", "proprietors lessee"
                  "proprietor in leasehold interest", "proprietors in leasehold interest",
                  "proprietor in freehold interest", "proprietors in freehold interest"]
    for toFind in strsToFind:
        if toFind in innerText:
            start = innerText.find(toFind)
            ret.append((start, start + len(toFind), 'OWNERSHIP STATUS'))
    return ret
    


# In[28]:


def removeOverlapsAndBadEntries(tupleTags):
    """Remove tuples that reprsenting taggings of entities so that no two tuples overlap
    concerning the characters they use in the original text.
    
    args: 
    tupleTags: list of three-tuples in format required by spaCy for training data.
    
    returns: list of three-tuples in format required by spaCy for training data, overlaps removed."""
    
    charsUsedOverall = set()
    overlapTagNums = []
    
    #find tag num which overlaps with previous tags
    for tagNum in range(len(tupleTags)):
        tag = tupleTags[tagNum]
        start = tag[0]
        end = tag[1]
        charsUsedOneTag = set()
        
        if start == -1:
            overlapTagNums.append(tagNum)
            continue
        
        for char in range(start, end):
            charsUsedOneTag.add(char)
        intersect = charsUsedOverall.intersection(charsUsedOneTag)
        if len(intersect) == 0:
            charsUsedOverall = charsUsedOverall.union(charsUsedOneTag)
        else:
            overlapTagNums.append(tagNum)
    
    #remove overlapping tags
    for tagNum in reversed(overlapTagNums):
        tupleTags.pop(tagNum)
    return tupleTags

def getListOfDistricts():
    """From the csv Kenya_districts.csv, pull a python list of Kenyan districts.
    
    returns: a Python list of districts in Kenya."""
    
    os.chdir(UTILDIR)
    df = pd.read_csv('Kenya_districts.csv')
    districtsUncleaned = df[['DISTRICT']]['DISTRICT']
    cleanDistricts = [district[:-9] for district in districtsUncleaned]
    newDistricts = set(cleanDistricts)
    for district in cleanDistricts:
        if district[-4:] == "East" or district[-4:] == "West":
            newDistricts.add(district[:-5])
            continue 
        if district[-5:] == "North" or district[-5:] == "South":
            newDistricts.add(district[:-6])
    return newDistricts

DISTRICTS = getListOfDistricts()

def getDistrictTuple(innerText):
    """Pull all tuples representing districts in Kenya. 
    
    args:
    innerText: the text of a gazette segment, minus headers and footers.
    
    returns: a list of three-tuples required for spaCy training data (could be empty). """
    
    ret = []
    for district in DISTRICTS:
        if district in innerText:
            matches = re.finditer(district + " District", innerText)
            for match in matches:
                ret.append((match.start(), match.start() + len(district), 'DISTRICT'))
                
            matches = re.finditer("district of " + district, innerText)
            for match in matches:
                ret.append((match.start() + 12, match.start() + 12 + len(district), 'DISTRICT'))
    return ret

def getLocationTuple(innerText):
    """Pull the phrase '(situate in ...), in the district of ...'. 
    
    args:
    innerText: the text of a gazette segment, minus headers and footers.
    
    returns: a list of three-tuples required for spaCy training data (could be empty). """
    
    ret = []
    try:
        strToFind = re.search(r"situate (.{8,}) in", innerText)[1]
        start = innerText.find(strToFind)
        #print(start, strToFind)
        ret.append((start, start + len(strToFind), 'LOC'))
        return ret
    except:
        return ret


# In[29]:


def getIDtuple(nameText, firstCharI):
    """Pull the phrase 'ID/12312' (digits can change of course).
    Return in tuple format required by spaCy. 
    
    args:
    nameText: text of a name pulled, which might also contain an ID number inside.
    firstCharI: the index inside the original text in which the name starts."""
    
    try:
        strToFind = re.search(r"\((ID/[0-9]{3,})\)", nameText)[1] # 3 is a magic number
        start = nameText.find(strToFind)
        #print(start, strToFind)
        return (firstCharI + start, firstCharI + start + len(strToFind), 'ID')
    except:
        return None
        
def stripIDsFromPersonTuples(personTuples, innerText):
    """Given a list of tuples which represent the person entities in the text,
    extract their corresponding ID numbers.
    
    personTuple: three tuple required by spaCy format.
    innerText: the text of a gazette segment, minus headers and footers."""
    
    ret = []
    for tup in personTuples:
        start, end, ID = tup
        if ID != "PERSON":
            ret.append(tup)
            continue
        nameText = innerText[start:end]
        IDtuple = getIDtuple(nameText, start)
        if IDtuple:
            newEnd = nameText.find("(")
            ret.append((start, start + newEnd, 'PERSON'))
            ret.append(IDtuple)
        else:
            ret.append(tup)
    return ret


# In[30]:


def getAllTrainData(df):
    """Gets all training data required by spaCy for one preprocessing csv. 
    Returns in list format which spaCy desires.
    
    args:
    df: pandas df representing one regex-extracted entites csv.
    
    returns: a list of tuples of the format (innerText, retDict). 
    Each list item corresponds to the data structure found at the top of this notebook."""
    
    ret = []
    mask = getMaskOfGoodCols(df)
    for i in range(len(df)):
        if mask[i]:
            series = df.iloc[i,]
            ret.append(getTrainDataOneSeries(series))
    return ret

def getTrainDataOneSeries(series):
    """For one series (entry) in a Pandas df, get all training data in format required by spaCy.
    
    args:
    series: row of a a pandas dataframe representing a pre-processed gazette.
    
    returns: (innerText, retDict). This corresponds to the data structure found
    at the top of this notebook."""
    
    innerText = series['inner text']
    value = getTupleTag(series, 'land size', 'LAND SIZE')
    value += getTupleTag(series, 'title number', "LAND REGISTRATION")
    value += getTupleTag(series, 'LR number', 'LAND REGISTRATION')
    value += getTupleTag(series, 'plot number', "LAND REGISTRATION")
    value += getTupleTag(series, 'grant number', "LAND REGISTRATION")
    value += getDeedStatus(innerText)
    value += getOwnershipStatus(innerText)
    value += getOwnerTuple(series)
    value += getOwnerAddressTuple(series)
    value += getDistrictTuple(innerText)
    value += getLocationTuple(innerText)
    value = stripIDsFromPersonTuples(value, innerText)
    removeOverlapsAndBadEntries(value)
    retDict = {'entities' : value}
    return (innerText, retDict)


# In[31]:


def exportTrainData(csvNum, writeToTxt = False, filename = 'default', filepath = 'default'):
    """Return training data in spaCy format for a single pre-processing csv.
    Export to txt if necessary.
    
    args:
    csvNum: index of pre-processing csv to use.
    writeToTxt: if true, write training data to txt format.
    filename: name of file to write txt to
    filepath: directory to write file to.
    
    returns: training data in the format shown at top of notebook."""
    
    df = readProcessedGazette(csvNum)
    trainData = getAllTrainData(df)
    
    if writeToTxt:
        # deal with writing to csv if necessary
        if filename == 'default':
            filename = 'train_data_' + listOfCsvsNew[csvNum][9:-4]
        if filepath == 'default':
            filepath = 'ERROR_PICK_DIRECTORY'
        os.chdir(filepath)
        trainText = str(trainData)
        setup.writeTxt(filename, trainText, filepath)
        
    return trainData


# In[32]:


def exportSeriesOfTrainData(startI, endI, writeToTxt = False):
    """Return training data in spaCy format for a range of pre-processing csvs.
    Export to txts if necessary.
    
    args:
    startI, endI: range of indices of pre-processing csvs to use (inclusive, exclusive).
    writeToTxt: if true, write training data to txt format.
    
    returns: training data in the format shown at top of notebook."""
    
    ret = []
    for i in range(startI, endI):
        ret += exportTrainData(i)
    return ret


# In[33]:


def pullFound(testSet):
    """Debugging method. Print the entities found in a text."""
    
    text = testSet[0]
    print(text + '\n')
    for entry in testSet[1]['entities']:
        start = entry[0]
        end = entry[1]
        print(entry[2] +": " + text[start:end])
    return

def skipNER(gazNum):
    """Debugging method. Extract entities that appear in training data."""
    
    segments = exportTrainData(gazNum)
    ret = []
    for segment in segments:
        segRet = []
        text = segment[0]
        for entry in segment[1]['entities']:
            start = entry[0]
            end = entry[1]
            typeStr = entry[2]
            itemStr = text[start:end]
            segRet.append([typeStr, itemStr])
        ret.append(segRet)
    return ret


# In[34]:


def pullOldGazetteSeg(gazetteNum, textOnly = True, 
                      titles = ['THE LAND ACT', 'THE NATIONAL LAND COMMISSION ACT', 
                                'THE ENIVONRMENTAL MANAGEMENT AND','THE LAND REGISTRATION ACT']):
    """Debugging method. Pull old gazette segments, containing only titles listed in titles."""

    df = readProcessedGazette(gazetteNum, newOnly = False)
    gazetteName = listOfCsvsOld[gazetteNum]
    if titles == 'all':
        return df, gazetteName
    ret = df[df['title'] == "never gonna see this!"]
    for title in titles:
        subtitlesArr = np.array(df['subtitles'])
        titlesArr = np.array(df['title'])
        inSubtitles = np.array([title in str(subtitlesArr[i]) for i in range(len(subtitlesArr))])
        inTitles = np.array([title in str(titlesArr[i]) for i in range(len(titlesArr))])
        goodEntries = np.logical_or(inSubtitles, inTitles)
        ret = ret.append(df[goodEntries])
    if textOnly:
        ret1 = list(ret['text'])
        ret2 = list(ret['inner text'])
        if ret1 == [] or type(ret1[0]) == float:
            return gazetteName, [], []
        else:
            return gazetteName, ret1, ret2
    else:
        return gazetteName, ret

def pullRangeOfOldGazettes(startGaz, endGaz, textOnly = True,
                           titles = ['THE LAND ACT', 'THE NATIONAL LAND COMMISSION ACT', 
                                     'THE ENIVONRMENTAL MANAGEMENT AND','THE LAND REGISTRATION ACT']):
    """Debugging method. Pull old gazette segments, containing only titles listed in titles."""
    
    ret = []
    for i in range(startGaz + 1, endGaz):
        newData = pullOldGazetteSeg(i, textOnly, titles)
        ret.append(newData)
    return ret

def inspectOldGazette(gazetteNum, titles = ['THE LAND ACT', 'THE NATIONAL LAND COMMISSION ACT', 
                                'THE ENIVONRMENTAL MANAGEMENT AND','THE LAND REGISTRATION ACT']):
    """Debugging method. Print output of an old gazette."""
    
    name, segsFull, segsInner = pullOldGazetteSeg(gazetteNum, True, titles)
    print(name)
    for i in range(len(segsFull)):
        print("FULL")
        print(segsFull[i])
        print("INNER")
        print(segsInner[i])
        print("\n\n_______\n\n")
        
        
def inspectRangeOfOldGazettes(startGaz, endGaz, titles = ['THE LAND ACT', 'THE NATIONAL LAND COMMISSION ACT', 
                                'THE ENIVONRMENTAL MANAGEMENT AND','THE LAND REGISTRATION ACT']):
    """Debugging method. Print output of many old gazettes."""
    # Third act is the "Environmental Management and Conservation Act (2015) (EMCA)"
    
    for i in range(startGaz, endGaz):
        inspectOldGazette(i, titles)


# In[ ]:





# In[ ]:





# In[ ]:




