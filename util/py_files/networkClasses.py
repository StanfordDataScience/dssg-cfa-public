#!/usr/bin/env python
# coding: utf-8

# In[4]:


# -----------------------------------------------------------
# Create Python objects (classes) which hold relevant information extracted
# from gazette segments. These classes will be the ground work for our network.
# 
# Written primarily by Robbie (thus far)
# -----------------------------------------------------------


# In[5]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
UTILDIR = ROUTETOROOTDIR + 'util'
JSONSDIR = ROUTETOROOTDIR + 'A_pdf_to_text/jsons_ke_gazettes/'
CSVTRAINDIR = ROUTETOROOTDIR + 'B_text_preprocessing/csv_outputs_train/'
CSVTESTDIR = ROUTETOROOTDIR + 'B_text_preprocessing/csv_outputs_test/'
import os
import re
import numpy as np
            
os.chdir(IMPORTSCRIPTSDIR)
import trainingDataForSpaCy
import C_exportNERAPI
import setup


# It will be helpful to describe the format that spaCy outputs entity data in for a single segment. Below is an example:
# 
# \[('PERSON', 'Dekha Sheikh'),
# 
#  ('OWNER ADDRESS', 'P.O. Box 614–00606, Nairobi in the Republic of Kenya'),
#  
#  ('OWNERSHIP STATUS', 'proprietor lessee'),
#  
#  ('CARDINAL', 'A4'),
#  
#  ('GPE', 'Block'),
#  
#  ('ORG', 'Third Floor'),
#  
#  ('LAND REGISTRATION', 'L.R. number 209/10345/9'),
#  
#  ('LOC', 'in the city of Nairobi'),
#  
#  ('LOC', 'the Nairobi Area'),
#  
#  ('CARDINAL', '106703/1'),
#  
#  ('DEED STATUS', 'lost'),
#  
#  ('DATE', '60) days')\]
# 
# Each item in the outer list is an entity found within a single segment. Each inner tuple contains two items: first, the spaCy tag for the type of entity, and second, the string representing that entity. A general format is as follows:
# 
# \[TAG, string),
# 
#  (TAG, string), 
#  
#  ... \]

# In[6]:


def disambiguateOwnerAddress(ownerAddresses):
    """Our NER has a problem: it identifies merely a district as the address 
    of a person or organization. This method is meant to solve this problem by 
    determining if the text contains a district, an address, or both.
    
    args:
    ownerAddress: a list of strings representing potential addresses.
    
    returns: (addressret, districtStrs)
    addressRet: the longest (presumably most detailed) address.
    districtStrs: a list of districts found in this persons' addresses."""
    
    addressStrs = []
    districtStrs = []
    for address in ownerAddresses:
        if "P.O. Box" in address:
            addressStrs.append(address)
        for district in trainingDataForSpaCy.DISTRICTS:
            if district in address:
                districtStrs.append(district)
                
    if addressStrs == []:
        addressRet = None
    else:
        addressRet = getLongestStr(addressStrs)
    if districtStrs == []:
        districtStrs = None
    return addressRet, districtStrs

def getLongestStr(textList):
    """Return the string that is the longest in textList"""
    
    best = textList[0]
    bestLen = 0
    for text in textList:
        if len(text) > bestLen:
            best = text
            bestLen = len(text)
    return best


# In[7]:


class personNode(object):
    """Class to represent an individual. 
    Also represents a node in our network graph."""
    
    def __init__(self, nameInit = None, addressInit = None, IDInit = None, UIDInit = None):
        self.name = nameInit
        self.address, self.district = disambiguateOwnerAddress(addressInit)
        self.ID = IDInit
        self.UID = UIDInit
        
    def __str__(self):
        ret = "Person node: \n"
        if self.name:
            ret += "Name: " + self.name + ".\n"
        if self.address:
            ret += "Address: " + str(self.address) + ".\n"
        if self.district:
            ret += "District: " + str(self.district) + '.\n'
        return ret

class orgNode(object):
    """Class to represent an organization. 
    Also represents a node in our graph."""
    
    def __init__(self, nameInit = None, addressInit = None, UIDInit = None):
        self.name = nameInit
        self.address, self.district = disambiguateOwnerAddress(addressInit)
        self.UID = UIDInit
        
    def __str__(self):
        ret = "Org node: \n"
        if self.name:
            ret += "Name: " + self.name + ".\n"
        if self.address:
            ret += "Address: " + str(self.address) + ".\n"
        if self.district:
            ret += "District: " + str(self.district) + '.\n'
        return ret

        
        
class landNode(object):
    """Class to represent a plot of land (or apartment, etc.). 
    Also represents a node in our graph."""
    
    def __init__(self, size = None, loc = None, LRs = None, district = None, UIDInit = None):
        self.LRs = LRs
        self.location = loc
        self.size = size
        self.district = district
        self.UID = UIDInit
        
    def __str__(self):
        ret = "Land node: \n"
        for LR in self.LRs:
            ret += "Land Registration: " + LR + ".\n"
        if self.location:
            ret += "Location: " + self.location + ".\n"
        if self.size:
            ret += "Size: " + self.size + ".\n"
        if self.district:
            ret += "District: " + self.district + ".\n"
        return ret
        
        
class landOrgEdge(object):
    """Class to represent a relationship between a person or org and a plot of land.
    Also represents an edge in our graph."""
    
    def __init__(self, deedStatusInit = None, ownershipStatusInit = None, 
                 dateOfAnnouncement = None, MRnum = None,
                 signatorObj = None, landObj = None, orgOrPersonObj = None):
        self.deedStatus = deedStatusInit
        self.ownershipStatus = ownershipStatusInit
        self.date = dateOfAnnouncement
        self.MR = MRnum   
        
    def __str__(self):
        ret = "Edge between person or organization and land.\n"
        if self.deedStatus:
            ret += "Deed Status: " + str(self.deedStatus) + ".\n"
        if self.ownershipStatus:
            ret += "Ownership Status: " + self.ownershipStatus + ".\n"
        if self.date:
            ret += "Date of Announcement: " + self.date + ".\n"
        if self.MR:
            ret += "MR Number: " + self.MR + ".\n"
        return ret
    
        
class signator(object):
    """Class to represent a signator."""
    
    def __init__(self, nameInit = None, locationInit  = None, roleInit  = None):
        self.name = nameInit
        self.location = locationInit
        self.role = roleInit
        
    def __str__(self):
        ret = "Signator object. \n"
        if self.name:
            ret += "Name: " + self.name + '\n'
        if self.location:
            ret += "Location: " + str(self.location) + '\n'
        if self.role:
            ret += "Role: " + str(self.role) + '\n'
        return ret
        


# In[8]:


def extractEntityType(entities, typeStr, rmFromList = False):
    """From a list where the inner tuples are pairs of entity type and corresponding string,
    extract all inner tuples of the type requested in typstr. 
    
    args: nested list of entities as described at top o notebook.
    typeStr: spaCy tag for the type of entity to pull.
    rmFromList: If rmFromList is true, then remove inner tuples from the outer nested list if returning.
    
    returns: list of inner tuples with appropriate tag."""
    
    ret = []
    for i in range(len(entities) - 1, -1, -1):
        entity = entities[i]
        if entity[0] == typeStr:
            ret.append(entity)
            if rmFromList:
                entities.pop(i)
    return ret


def createPeopleAndOrgObjs(people, orgs, address, ids):
    """Given the people and address strings from spaCy, return a list of 
    people and organization nodes.
    
    args:
    people: list of PERSON tuples in format shown at top of notebook.
    ors: list of ORG tuple in format shown at top of notebook.
    address: list of OWNER ADDRESS tuples in format shown at top of notebook.
    ids: list of ID tuples in format shown at top of notebook.
    
    returns: a list of personNode and orgNode objects."""
    
    ret = []
    addresses = [entry[1] for entry in address]
    for i in range(len(people)):
        person = people[i]
        name = person[1]
        try:
            # we are counting on IDs being in order!
            ID = ids[i][1]
        except:
            ID = None        
        ret.append(personNode(name, addresses, ID))
        
    for org in orgs:
        name = org[1]
        ret.append(orgNode(name, addresses))
    return ret

def getFirstEntryIfAvailable(listEntries):
    """Helper method. Retrieves second entry of the tuple of the first entry of a list,
    if it is available. Otherwise returns None. """
    
    if listEntries:
        return listEntries[0][1]
    else:
        return None

def createLandObj(sizes, locs, LRs, districts):
    """Given strings to represent each characteristic of land, create a land object.
    
    args:
    sizes: list of LAND SIZE tuples in format shown at top of notebook.
    locs: list of LOC tuples in format shown at top of notebook.
    LRs: list of LAND REGISTRATION tuples in format shown at top of notebook.
    districts: list of DISTRICT tuples in format shown at top of notebook.
    
    returns: a landNode object."""
    
    size = getFirstEntryIfAvailable(sizes)
    loc = getFirstEntryIfAvailable(locs)
    LRlist = []
    for LR in LRs:
        LRlist.append(LR[1])
    districtsClean = [district[1] for district in districts]
    districtsClean = (list(set(districtsClean)))
    if len(districtsClean) == 1:
        district = districtsClean[0]
    else:
        district = None
    return landNode(size, loc, LRlist, district)

def isFloat(obj):
    """Given an object, return True if it is a Python float or a numpy float (64).
    The reason this method exists is that when Pandas reads a csv it assumes that an
    empty cell is a float with value NaN, instead of an empty string. We want to catch 
    this by finding floats when we are looking for a string."""
    
    return type(obj) == float or type(obj) == np.float64

def createEdgeObjs(deedStatus, ownershipStatus, series):
    """Given strings and nodes to represent each characteristic, create an edge object.
    
    args:
    deedStatus: list of DEED STATUS tuples in format shown at top of notebook.
    ownershipStatus: list of OWNERSHIP STATUS tuples in format shown at top of notebook.
    series: data from one row of pre-processing csv.
    
    returns a landOrgEdge object."""
    
    deedStatus = [status[1] for status in deedStatus]
    ownershipStatus = getFirstEntryIfAvailable(ownershipStatus)
    date = series['date']
    MR = series['MR number']
    if isFloat(date):
        date = None
    if isFloat(MR):
        MR = None
    
    return landOrgEdge(deedStatus, ownershipStatus, date, MR)

def createSignatorObj(series):
    """Create a signator object given a row from the pre-processing csv.
    
    args:
    series: a row from the pre-processing csv.
    
    returns: a signator object."""
    name = series['signator']
    loc = series['signator location']
    role = series['signator role']
    
    if isFloat(name): name = None 
    if isFloat(loc): loc = None 
    if isFloat(role): role = None 
    
    return signator(name, loc, role)

def processNERSegment(entities, series):
    """Given a list of entities extracted from text, create nodes and edges for a graph.
    
    args:
    entiries: list output shown at top of notebook.
    series: a row from pre-processing csv.
    
    returns: (peopleObjs, landObj, edgeObj, signatorObj)
        peopleObjs: a list of personNode and orgNode objects.
        landObj: a landNode object.
        edgeObj: a landOrgEdge object.
        signatorObj: a signator object."""
    
    # create people and organizations
    people = extractEntityType(entities, "PERSON")
    address = extractEntityType(entities, "OWNER ADDRESS")
    orgs = extractEntityType(entities, "ORG")
    ids = extractEntityType(entities, "ID")
    peopleObjs = createPeopleAndOrgObjs(people, orgs, address, ids)
    
    #create plot of land
    sizes =  extractEntityType(entities, "LAND SIZE")
    LRs = extractEntityType(entities, "LAND REGISTRATION")
    locs = extractEntityType(entities, "LOC")
    districts = extractEntityType(entities, "DISTRICT")
    landObj = createLandObj(sizes, locs, LRs, districts)
    
    #create signator
    signatorObj = createSignatorObj(series)
    
    #create edge between people or orgs and plot
    deedStatus = extractEntityType(entities, "DEED STATUS")
    ownershipStatus = extractEntityType(entities, "OWNERSHIP STATUS")
    edgeObj = createEdgeObjs(deedStatus, ownershipStatus, series)
                               
    return (peopleObjs, landObj, edgeObj, signatorObj)

def printResults(results):
    """Helper method. Given the results of a call to 
    processNERsegment, print them out. """
    
    for result in results:
        if (type(result) == list):
            for node in result:
                print(str(node))
        else:
            print(str(result))
            
def getAllDataOneGazette(gazetteNum):
    """For one gazette, return NER output and csv output.
    
    args:
    gazetteNum: the index of the gazette to be found in the directory trainingDataForSpaCy.CSVTRAINDIR
    
    returns: (entities, csvRow)
    entities: output of spaCy. Nested list shown at top of notebook.
    csvRow: row from the preprovessing csv. Can be used like a dictionary."""
    
    NERoutput = C_exportNERAPI.getNEROutput(gazetteNum)
    csvData = trainingDataForSpaCy.readProcessedGazette(gazetteNum)
    return [(NERoutput[i], csvData.iloc[i]) for i in range(len(NERoutput))]

def compareTrainDataToSpacyOutput(gazetteNum, segNum):
    """Debugging method. For a given gazette number and segment number, 
    compare the entities extracted by regex to the entities extracted by spaCy."""
    
    trainData = trainingDataForSpaCy.skipNER(gazetteNum)[segNum]
    trainData = [tuple(datapoint) for datapoint in trainData]
    NERoutput = C_exportNERAPI.getNEROutput(gazetteNum)[segNum]
    
    bothFound = []
    for trainEnt in trainData:
        if trainEnt in NERoutput:
            bothFound.append(trainEnt)
            
    print("BOTH FOUND:")
    for ent in bothFound:
        print(ent)
    
    print("JUST IN TRAIN DATA:")
    for ent in trainData:
        if ent not in bothFound: print(ent)
            
    print("JUST IN SPACY DATA:")
    for ent in NERoutput:
        if ent not in bothFound: print(ent)
            
    print("TEXT:")
    print(C_exportNERAPI.getListOfTexts(gazetteNum)[segNum])
    return None


# In[ ]:





# In[ ]:





# In[ ]:




