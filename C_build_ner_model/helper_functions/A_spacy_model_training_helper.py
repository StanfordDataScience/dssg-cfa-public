#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -------------------------------------------
#
# This file contains helper functions to train a modified spaCy NER model  
# using training segments extracted from the Kenya gazettes.
#
# -------------------------------------------


# In[ ]:


# Keep these in a separate chunk otherwise you get error
from __future__ import unicode_literals, print_function

import plac
import random
import warnings
from pathlib import Path
import spacy
from spacy import displacy
from spacy.util import minibatch, compounding

from tqdm import tqdm


# In[ ]:


# Helper Functions


# In[2]:


def trainModifiedNERModel(training_data, all_labels=[], model=None, new_model_name="modified_ner_model_gazettes", output_dir=None, n_iter=10):
    """
    A function to train a modified NER model using custom training data. This function was copied and modified from https://spacy.io/usage/training
    
    Arguments:
    training_data -- list of training samples. Each training sample is a list in the form [TEXT, {'entities': (START_CHAR, END_CHAR, LABEL)}]
    model -- a string specifying the base model. If None, the model will be constructed from scratch.
    new_model_name -- a string specifying the desired new model name
    output_dir -- a string to the directory where the new model should be stored
    n_iter -- an int specifying the number of iterations for model training
    
    Output:
    'Model Trained and Saved.' -- a string confirming that the model training is completed. 
    """
    
    random.seed(0)
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model, if there is any
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank("en")  # create blank Language class
        print("Created blank 'en' model")
    # Add entity recognizer to model if it's not in the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner)
        
    # otherwise, get it, so we can add labels to it
    else:
        ner = nlp.get_pipe("ner")

    # add new entity label to entity recognizer    
    for i in all_labels:
        ner.add_label(i)
    
    
    if model is None:
    #if model is None:
        optimizer = nlp.begin_training()
    else:
        optimizer = nlp.resume_training()
    move_names = list(ner.move_names)
    # get names of other pipes to disable them during training
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    # only train NER
    with nlp.disable_pipes(*other_pipes), warnings.catch_warnings():
        # show warnings for misaligned entity spans once
        warnings.filterwarnings("once", category=UserWarning, module='spacy')

        sizes = compounding(1.0, 4.0, 1.001)
        # batch up the examples using spaCy's minibatch
        for itn in range(n_iter):
            random.shuffle(training_data)
            batches = minibatch(training_data, size=sizes)
            losses = {}
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)
            print("Losses", losses)
 
    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.meta["name"] = new_model_name  # rename model
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)
        
    
    return "Model Trained and Saved."


# In[3]:


def removeOverlapsAndBadEntries(tupleTags):
    """
    A function to remove tuples that represent entity tags so that no two tuples overlap
    concerning the characters they use in the original text.
    
    Arguments:
    tupleTags -- a tuple of entities of entities of the form (START_CHAR, END_CHAR, LABEL)
    
    Returns:
    tupleTags -- a tuple of entities of entities of the form (START_CHAR, END_CHAR, LABEL) with overlapping tags removed    
    """
    
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


# In[4]:


def getAllLabels(modified_labels):
    """
    A function that combines standard labels that are default to the spacy model and modified labels that the user wants to train.
    
    Arguments:
    modified_labes -- a list of the modified labels in CAPS the user wants to add to the model.
    
    Returns:
    all_labels -- a list of all labels for the model to be trained on.    
    """
    
    standard_labels = [
    'PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 
    'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL'
    ]
    
    all_labels = all_labels = standard_labels + modified_labels
    
    return all_labels
    


# In[1]:


def getDefaultAndModifiedLabels(default_label_trainings, modified_label_trainings):
    """
    A function that combines the combines the default spaCy labels and the modified labels for training texts.
    Each training text has the modified labels (such as LAND SIZE) extracted manually.
    But, the same text is also run through the default spaCy NER model to counteract the catastrophic forgetting
    problem described here: https://explosion.ai/blog/pseudo-rehearsal-catastrophic-forgetting
    
    
    Arguments:
    default_label_trainings -- a list of training texts with their default labels in the form (TEXT, {'entities': [(START_CHAR, END_CHAR, LABEL)]})
    modified_label_trainings -- a list of training texts with their modified labels in the form (TEXT, {'entities': [(START_CHAR, END_CHAR, LABEL)]})
    
    Returns:
    all_train_data -- a list containing a text with its default and modified labels with the overlaps removed in the form (TEXT, {'entities': [(START_CHAR, END_CHAR, LABEL)]})
    
    """
    
    all_train_data = []
    for i in range(len(modified_label_trainings)):
        per_ent_labels = modified_label_trainings[i][1]['entities'] + default_label_trainings[i][1]['entities']
        unique_labels = removeOverlapsAndBadEntries(per_ent_labels) #to remove duplicate labels
        an_entry = [default_label_trainings[i][0], {'entities': unique_labels}]
        all_train_data.append(an_entry)
        
    return all_train_data
    


# In[ ]:




