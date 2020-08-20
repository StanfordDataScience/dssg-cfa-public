#!/usr/bin/env python
# coding: utf-8

# In[12]:


# -----------------------------------------------------------
# Create an API to pull entities using our spaCy model.
# 
# Written primarily by Robbie, who stole T's code from file B
# -----------------------------------------------------------


# In[13]:


import os
import spacy

ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
local_output_dir = ROUTETOROOTDIR + "C_build_ner_model/model_outputs/"

os.chdir(IMPORTSCRIPTSDIR)
import trainingDataForSpaCy


# In[14]:


os.chdir(local_output_dir)
nlp = spacy.load(local_output_dir)   # load the model


# In[9]:


def getListOfTexts(gazetteNum):
    """API to training data for spaCy: returns a list of all inner texts from a given gazette.
    
    args:
    gazetteNum: index of pre-processing gazette from list within trainDataForSpaCy.
    
    returns: list, each entry of which is an inner text (cleaned, no headers or footers)."""
    
    return [data[0] for data in trainingDataForSpaCy.exportTrainData(gazetteNum)]

def getNEROutput(gazetteNum):
    """For a given gazette number, call spaCy NER on each segment and return the outputs.
    
    args:
    gazetteNum: index of pre-processing gazette from list within trainDataForSpaCy.
    
    returns: a nested list.
        Outer list: each item contains NER outputs for one segment.
        inner list: each item is an NER tag for a single segment in tuple format.
        items in inner list: (label, text)
            label: entity tag
            text: text corresponding to said tag."""
    
    rawText = getListOfTexts(gazetteNum)
    docs = [nlp(segment) for segment in rawText]
    ret = []
    for doc in docs:
        ret.append([(ent.label_, ent.text) for ent in doc.ents])
    return ret


# Below is a demonstration of all that this file does. It simply calls the spaCy model, but using the 'inner text' column of the pre-processing gazettes that we created in part B (text preprocessing).

# In[16]:


#getNEROutput(0)[0]


# In[ ]:




