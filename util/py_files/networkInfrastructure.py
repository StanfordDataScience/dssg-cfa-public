#!/usr/bin/env python
# coding: utf-8

# In[2]:


# -----------------------------------------------------------
# Create the large data structures which will represent a graph efficiently
# and allow for efficient adding of new nodes and edges.
# 
# Written primarily by Robbie (thus far)
# -----------------------------------------------------------


# In[3]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
UTILDIR = ROUTETOROOTDIR + 'util'
JSONSDIR = ROUTETOROOTDIR + 'A_pdf_to_text/jsons_ke_gazettes/'
CSVTRAINDIR = ROUTETOROOTDIR + 'B_text_preprocessing/csv_outputs_train/'
CSVTESTDIR = ROUTETOROOTDIR + 'B_text_preprocessing/csv_outputs_test/'
NETWORKOUTPUTDIR = ROUTETOROOTDIR + 'D_build_network/network_outputs/'
import os
import re
import random
            
    
os.chdir(IMPORTSCRIPTSDIR)
import trainingDataForSpaCy
import setup
os.chdir(IMPORTSCRIPTSDIR)
import networkClasses


# It will be helpful to describe the data structures in this file so that the functions below operating on them make sense.
# 
# GLOBAL_UID is simply the lowest positive int that hasn't been used as an identifier. It steadily increases as the program runs.
# 
# GLOBAL_NODES_DICT is a hashmap storing all the nodes of the graph. The keys to the hash are a name (in the case of a person or organization) or simply a unique number (in the case of a plot of land). Later work might determine a more relevant key for a plot of land to hash on. Because two individuals might share a name while being different persons with different ID numbers, the value for each key in the hash table is a list. Each item in this list contains one node object, either a personNode, orgNode, or landNode (all from networkClasses.py). 
# 
# Because values in our nodes hashtable are lists, to uniquely identify each node in our graph we must give both a hashkey (a name or unique number in this case) and a list index (almost always 0). This combination is what is later referred to in variable names as a fullKey, and uniquely identifies each node. fullKey is defined nowhere (it is really just a tuple), but it is helpful to think of as its own type of object in order to understand the code fully.
# 
# GLOBAL_EDGES_DICT is a hashmap storing all the edges in a graph. The key is simply a unique number, while the value is a four-tuple, fullKey1, fullKey2, signatorKey, edgeObj). fullKey1, fullKey2, and signatorKey are all fullKey objects, the first two to GLOBAL_NODES_DICT and the third to GLOBAL_SIGNATORS_DICT.
# 
# GLOBAL_SIGNATORS_DICT cannot have duplicate names, but for the sake of convention it keys are still names and its values are still lists, this time of signator objets from networkClasses.py. As a result, it still uses the fullKey convention when being referred to in other places.
# 
# GLOBAL_DISTRICTS_DICT contains district names as keys, and a list of fullKeys of nodes (person, org, or land) as values. It is used to create edges between nodes sharing a district.
# 
# GLOBAL_ADDRESSES_DICT contains address as keys and a list of fullKeys of nodes as values. It is used to create edges between nodes sharing an address.
# 
# When an 'owner' is reference, this refers to a personNode or an orgNode object.

# In[4]:


GLOBAL_UID = 0
GLOBAL_EDGES_DICT = {}
GLOBAL_NODES_DICT = {}
GLOBAL_SIGNATORS_DICT = {}
GLOBAL_DISTRICTS_DICT = {}
GLOBAL_ADDRESSES_DICT = {}



def resetGlobalVals():
    """Reset all of the global values in this script."""
    
    global GLOBAL_NODES_DICT
    global GLOBAL_EDGE_SDICT
    global GLOBAL_UID
    global GLOBAL_SIGNATORS_DICT
    global GLOBAL_DISTRICTS_DICT 
    global GLOBAL_ADDRESSES_DICT 
    GLOBAL_UID = 0
    GLOBAL_EDGES_DICT = {}
    GLOBAL_NODES_DICT = {}
    GLOBAL_SIGNATORS_DICT = {}
    GLOBAL_DISTRICTS_DICT = {}
    GLOBAL_ADDRESSES_DICT = {}
    
def printGlobalVals(verbose = False):
    """Debugging method. Print all of the global values in this script."""
    
    print("Current UID: " + str(GLOBAL_UID))
    
    print('\n\nNum Edges: ' + str(len(GLOBAL_EDGES_DICT)))
    if verbose:
        print('\n\nedges dict: ')
        printDictWithValueAsList(GLOBAL_EDGES_DICT)
    
    print('\n\nNUM NODES: ' + str(len(GLOBAL_NODES_DICT)))
    if verbose:
        print('nodes dict')
        printDictWithValueAsList(GLOBAL_NODES_DICT)
    
    print('\n\nNum Signators: ' + str(len(GLOBAL_SIGNATORS_DICT)))
    if verbose:
        print('\n\nsignators dict: ')
        printDictWithValueAsList(GLOBAL_SIGNATORS_DICT)
    
    numObjsInDistricts = 'unknown'
    print('\n\nNum Objects in with Districts: ' + numObjsInDistricts)
    if verbose:
        print('\nDistricts Dict:')
        printDictWithValueAsList(GLOBAL_DISTRICTS_DICT)
    
def printDictWithValueAsList(dicto):
    """Debugging method.
    Print a dictionary with the structure seen in all of our global structures."""
    
    for val in dicto.values():
        for obj in val:
            print(obj)


# In[5]:


def incorporateGazette(gazetteNum):
    """Add the data from a single gazette to our global data structures in this script.
    
    args:
    gazetteNum: the index of the gazette to be found in the directory trainingDataForSpaCy.CSVTRAINDIR"""
    
    data = networkClasses.getAllDataOneGazette(gazetteNum)
    for NERout, series in data:
        ownerObjs, landObj, edgeObj, signatorObj = networkClasses.processNERSegment(NERout, series)
        ownerKeys = [addPersonOrOrgToGraph(owner) for owner in ownerObjs]
        landKey = addLandToGraph(landObj)
        signatorKey = addSignatorToGraph(signatorObj)
        addEdgesNewSegment(ownerKeys, landKey, signatorKey, edgeObj)

def addEdgesNewSegment(ownerKeys, landKey, signatorKey, edgeObj):
    """Create edges between the plot of land and each owner mentioned.
    
    args: 
    ownerKeys: list of fullKey objects of owners.
    landKey: fullKey objects of a land node.
    signatorKey: fullKey object of a signator.
    edgeObj: landOrgEdge object."""
    
    global GLOBAL_UID, GLOBAL_EDGES_DICT
    
    for ownerKey in ownerKeys:
        UID = GLOBAL_UID
        GLOBAL_UID += 1
        GLOBAL_EDGES_DICT[UID] = (ownerKey, landKey, signatorKey, edgeObj)
        
def addPersonOrOrgToGraph(ownerObj):
    """Add a person or org object to our hashmap storing these objects.
    Note that we are hashing based on the person's name. 
    
    args:
    ownerObj: orgNode or personNode object.
    
    returns: fullKey object for the argument."""
    
    global GLOBAL_NODES_DICT
    
    key = ownerObj.name
    if key in GLOBAL_NODES_DICT.keys():
        return checkForDuplicateOwner(ownerObj)
    else:
        GLOBAL_NODES_DICT[key] = [ownerObj]
        return(key, 0)
    
def addSignatorToGraph(signatorObj):
    """Add a signator object to our hashmap storing these objects.
    Note that we are hashing based on the signator's name. 
    
    args:
    signatorObj: signator object.
    
    returns: fullKey object for the argument."""
    
    global GLOBAL_SIGNATORS_DICT
    
    key = signatorObj.name
    if not key:
        return None
    if key in GLOBAL_SIGNATORS_DICT.keys():
        oldSig = GLOBAL_SIGNATORS_DICT[key][0]
        combineSignatorInstances(oldSig, signatorObj)
    else:
        GLOBAL_SIGNATORS_DICT[key] = [signatorObj]
    return (key, 0)
    
def checkForDuplicateOwner(ownerObj):
    """Check to see if a person or organization is already in our hashtable of entities.
    If they are already in the hash table, do not create a new entry (merge). Otherwise create new.
    Two entities count as duplicates if they share a name and an ID number, or have no ID number (both).
    
    args:
    ownerObj: orgNode or personNode object.
    
    returns: fullKey object for the argument."""
    
    global GLOBAL_NODES_DICT
    
    key = ownerObj.name
    matches = GLOBAL_NODES_DICT[key]
    addType = type(ownerObj)
    
    # try to merge person or org with a corresponding one
    for i in range(len(matches)):
        match = matches[i]
        origType = type(match)
        if addType == origType:
            if origType == networkClasses.orgNode:
                combineOrgInstances(match, ownerObj)
                return(key, i)
            elif origType == networkClasses.personNode and match.ID == ownerObj.ID:
                combinePersonInstances(match, ownerObj)
                return(key, i)
    
    # could not merge person or org with another, just add it normally
    GLOBAL_NODES_DICT[key].append(ownerObj)
    return (key, len(matches))

def combineOrgInstances(org1, org2):
    """Given two organizations objects that match in name, merge them into one and return it.
    Also store this merged object inside the first argument. 
    
    args:
    org1, org2: orgNode objects
    
    returns: an orgNode object representing the two arguments merged."""
    
    address1 = toSet(org1.address)
    address2 = toSet(org2.address)
    org1.address = list(address1.union(address2))
    
    district1 = toSet(org1.district)
    district2 = toSet(org2.district)
    org1.district = list(district1.union(district2))
    return org1

def combinePersonInstances(person1, person2):
    """Given two person objects that match in name and ID, merge them into one and return it.
    Also store this merged object inside the first argument. 
    
    args:
    person1, person2: personNode objects
    
    returns: a personNode representing the two arguments merged."""
    
    address1 = toSet(person1.address)
    address2 = toSet(person2.address)
    person1.address = list(address1.union(address2))
    
    district1 = toSet(person1.district)
    district2 = toSet(person2.district)
    person1.district = list(district1.union(district2))
    return person1

def combineSignatorInstances(sig1, sig2):
    """Given two signator objects that match in name, merge them into one and return it.
    Also store this merged object inside the first argument.
    
    args:
    sig1, sig2: signator objects
    
    returns: a signator object representing the two arguments merged."""
    
    loc1 = toSet(sig1.location)
    loc2 = toSet(sig2.location)
    loc = list(loc1.union(loc2))
    role1 = toSet(sig1.role)
    role2 = toSet(sig2.role)
    role = list(role1.union(role2))
    sig1.location = loc
    sig1.role = role
    return sig1

def toSet(obj):
    """Convert an object to a set. Only caveat is that None will be converted to an empty set,
    and that a string will not separate into its characters. Helper method."""
    
    if obj == None:
        return set()
    if type(obj) == str:
        return set([obj])
    else:
        return set(obj)
    
def addLandToGraph(landObj):
    """Add land to our global data structures. 
    
    args: 
    landObj: a landNode object
    
    returns: a fullKey object to landNode."""
    
    global GLOBAL_UID
    landObj.UID = GLOBAL_UID
    GLOBAL_UID += 1
    
    key = landObj.UID
    GLOBAL_NODES_DICT[key] = [landObj]
    fullKey = (key,0)
    return fullKey

def createAddressDict():
    """Create a dictionary with address as key and list of keys to NODE_DICT as values.
    Store in GLOBAL_ADDRESS_DICT."""
    
    for key in GLOBAL_NODES_DICT:
        for i in range(len(GLOBAL_NODES_DICT[key])):
            fullKey = (key, i)
            node = GLOBAL_NODES_DICT[key][i]
            if type(node) != networkClasses.landNode and node.address and len(node.address) == 1:
                addToAddressesDict(node.address[0], fullKey)
                
def addToAddressesDict(address, fullKey):
    """Helper method. Add the fullKey given to the address given in our global structure."""
    
    global GLOBAL_ADDRESSES_DICT
    
    if address not in GLOBAL_ADDRESSES_DICT.keys():
        GLOBAL_ADDRESSES_DICT[address] = [fullKey]
    else:
        GLOBAL_ADDRESSES_DICT[address].append(fullKey)

def createDistrictsDict():
    """Create a dictionary with district as key and list of keys to NODE_DICT as values.
    Store in GLOBAL_DISRTICTS_DICT."""
    
    for key in GLOBAL_NODES_DICT:
        for i in range(len(GLOBAL_NODES_DICT[key])):
            fullKey = (key, i)
            node = GLOBAL_NODES_DICT[key][i]
            if node.district and len(node.district) == 1:
                addToDistrictsDict(node.district[0], fullKey)

def addToDistrictsDict(district, fullKey):
    """Helpter method. add the fullKey given to the district given in our global structure."""
    
    global GLOBAL_DISTRICTS_DICT
    
    if district not in GLOBAL_DISTRICTS_DICT.keys():
        GLOBAL_DISTRICTS_DICT[district] = [fullKey]
    else:
        GLOBAL_DISTRICTS_DICT[district].append(fullKey)
#incorporateGazette(0)


# In[6]:


PERSON_SIZE_CONSTANT = 1
LAND_UNKNOWN_SIZE_CONSTANT = 1
LAND_IND = 1
PERSON_IND = 2
ORG_IND = 3
def createNodesCsv(fileaddendum = ''):
    """Write the data structures in this notebook into a csv so that they can be used by graphViz.
    
    args:
    fileaddendum: string to append to 'nodes' in name of file written."""
    
    rows = [['key', 'Type', 'Land Size', 'Description']]
    for key in GLOBAL_NODES_DICT.keys():
        nodeList = GLOBAL_NODES_DICT[key]
        for i in range(len(nodeList)):
            node = nodeList[i]
            if type(node) == networkClasses.landNode:
                nodeType = LAND_IND
                if node.size:
                    try:
                        nums = re.search(r"(.*?) hect", node.size)[1]
                        landsize = str(nums)
                    except:
                        landsize = str(LAND_UNKNOWN_SIZE_CONSTANT)
                        print("bad land size string: " + node.size)    
                else:
                    landsize = LAND_UNKNOWN_SIZE_CONSTANT
            elif type(node) == networkClasses.personNode:            
                nodeType = PERSON_IND
                landsize = PERSON_SIZE_CONSTANT
            elif type(node) == networkClasses.orgNode:
                nodeType = ORG_IND
                landsize = PERSON_SIZE_CONSTANT
            else:
                assert(False)
            rows.append([str((key,i)), nodeType, landsize, str(node)])
    setup.writeToCsv('nodes' + fileaddendum, rows, NETWORKOUTPUTDIR)
    
OWNERSHIP_WEIGHT_CONSTANT = 1
SAME_DISTRICT_WEIGHT_CONSTANT = 0.01
SAME_ADDRESS_WEIGHT_CONSTANT= 0.5
    
def createEdgesCsv(fileaddendum = ''):
    """Write the data structures in this notebook into a csv so that they can be used by graphViz.
    
    args:
    fileaddendum: string to append to 'edges' in name of file written."""
    
    rows = [['key1', 'key2', 'Weight', 'Description', 'signator key', 'signator description']]
    for UID in GLOBAL_EDGES_DICT:
        ownerKey, landKey, signatorKey, edgeObj = GLOBAL_EDGES_DICT[UID]
        if signatorKey:
            signatorDescription = str(GLOBAL_SIGNATORS_DICT[signatorKey[0]][signatorKey[1]])
        else:
            signatorDescription = 'None'
        rows.append([str(ownerKey), str(landKey), str(OWNERSHIP_WEIGHT_CONSTANT), 
                     str(edgeObj), str(signatorKey), signatorDescription])
        
    rows += getLocationRows(GLOBAL_DISTRICTS_DICT, SAME_DISTRICT_WEIGHT_CONSTANT)
    rows += getLocationRows(GLOBAL_ADDRESSES_DICT, SAME_ADDRESS_WEIGHT_CONSTANT)
    setup.writeToCsv('edges'  + fileaddendum, rows, NETWORKOUTPUTDIR)
            
        
def getLocationRows(dicto, weight):
    """Helper method. Get the rows to put in a csv which represent edges between entities sharing a location."""
    
    rows = [] #[['key1', 'key2', 'Weight', 'Description', 'signator key', 'signator description']]
    for loc in dicto.keys():
        numEntities = len(dicto[loc])
        for i in range(numEntities):
            fullKey1 = dicto[loc][i]
            for j in range(i+1, numEntities):
                fullKey2 = dicto[loc][j]
                rows.append([str(fullKey1), str(fullKey2), str(weight), 
                             'Same location: ' + loc, '', ''])
    return rows
            
    
def saveState(fileaddendum = ''):
    """Write the data structures in this notebook into a csv so that they can be used by graphViz.
    
    args:
    fileaddendum: string to append to 'edges' or 'nodes' in name of file written."""
    
    createEdgesCsv(fileaddendum)
    createNodesCsv(fileaddendum)


# In[7]:


def saveGraph(gazetteSelection, districtEdges = True, addressEdges = True):
    """Create a graph using random gazettes and save the output to csvs.
    
    args:
    sizeSample: number of gazettes to pull info from for the graph.
    districtEdges: if true, draw edges between entities with the same district.
    addressEdges: if true, draw edges between entities with the same address."""
    
    resetGlobalVals()
    sizeSample = len(gazetteSelection)
    fileaddendum = "_" + str(sizeSample) + "_gazettes_included_"
    for i in gazetteSelection:
        incorporateGazette(i)
    if districtEdges:
        createDistrictsDict()
        fileaddendum += "district_edges_drawn_"
    else:
        fileaddendum += "no_district_edges_drawn_"
    if addressEdges:
        createAddressDict()
        fileaddendum += "address_edges_drawn_"
    else:
        fileaddendum += "no_address_edges_drawn_"
    saveState(fileaddendum)
    


# In[ ]:





# In[ ]:




