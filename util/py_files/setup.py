#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -----------------------------------------------------------
# Creating some basic functions that Robbie tends to use
# in his workflow throughout directories
#
# Written primarily by Robbie (thus far)
# -----------------------------------------------------------


# In[8]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
EXPORTDATADIR1 = ROUTETOROOTDIR + 'B_text_preproessing/csv_outputs/'
UTILDIR = ROUTETOROOTDIR + 'util'
JSONSDIR = ROUTETOROOTDIR + 'A_pdf_to_text/jsons_ke_gazettes/'
ADIR = ROUTETOROOTDIR + 'A_pdf_to_text/'
BDIR = ROUTETOROOTDIR + 'B_text_preprocessing/'
CDIR = ROUTETOROOTDIR + 'C_build_ner_model/'
DDIR = ROUTETOROOTDIR + 'D_build_network/'
import os            
import csv


# In[55]:


def convertToPy(filename, filepath):
    """Convert a jupyter notebook script into .py format.
    .py format of the notebook is always created in 'util/py_files'
    
    args:
    filename: the name of the jupyter notebook you are converting (also name for the py file conversion).
    filepath: directory to find the notebook in."""
    
    outputDir = UTILDIR + 'py_files'
    get_ipython().run_line_magic('cd', '{filepath}')
    get_ipython().system("jupyter nbconvert --output-dir={outputDir} --to python {filename}")
    
def convertToHTML(filename, filepath):
    """Convert a jupyter notebook script into .html format.
    .html format of the notebook is created in the same directory that it is found in.
    
    args:
    filename: the name of the jupyter notebook you are converting (also name for the py file conversion).
    filepath: directory to find the notebook in."""
    
    get_ipython().run_line_magic('cd', '{filepath}')
    get_ipython().system("jupyter nbconvert --to html {filename}")
    
def convertAll():
    """Convert all scripts written thus far into .py files so that they can be imported.
    Also convert all walkthrough notebooks into html format."""
    
    convertToPy("setup", UTILDIR)
    convertToPy("orderingText", ADIR)
    convertToPy("readingJsonsBulk", BDIR)
    convertToPy("retoolingSegmentation", BDIR)
    convertToPy("trainingDataForSpaCy", BDIR)
    convertToPy("C_exportNERAPI", CDIR)
    convertToPy("networkClasses", DDIR)
    convertToPy("networkInfrastructure", DDIR)
    convertToHTML("walkthrough_notebook", ADIR)
    convertToHTML("walkthrough_notebook", BDIR)
    convertToHTML("walkthrough_notebook", DDIR)
    
def writeToCsv(filename, lines, filepath):
    """Write a csv to @param filepath with name @param filename. 
    Each line is one entry of @param lines.
    
    args:
    filename: the name of the csv you are creating.
    lines: a list, each entry of which is one row in the csv.
        Each entry in the outer list is typicall a list in its own right,
        with each entry in each inner list occupying one cell.
    filepath: te directory to write this csv to."""
    
    get_ipython().run_line_magic('cd', '~')
    get_ipython().run_line_magic('cd', '{filepath}')
    if len(filename) < 5 or filename[-4:] != ".csv":
        filename = filename + ".csv"
    with open(filename, 'w', newline='') as csvfile:
        report = csv.writer(csvfile)
        for line in lines:
            print(line)
            report.writerow(line)
            
def writeTxt(filename, text, filepath):
    """Write a csv to @param filepath with name @param filename.
    
    args:
    filename: the name of the csv you are creating.
    text: a string to write to txt.
    filepath: te directory to write this csv to."""
    
    get_ipython().run_line_magic('cd', '{filepath}')
    if len(filename) < 5 or filename[-4:] != ".txt":
        filename = filename + ".txt"
    fileObj = open(filename, "w")
    fileObj.write(text)
    fileObj.close()


# In[58]:


#convertAll()
#convertToPy("setup")


# In[ ]:





# In[ ]:





# In[ ]:




