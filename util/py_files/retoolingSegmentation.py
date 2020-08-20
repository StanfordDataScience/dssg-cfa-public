#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -----------------------------------------------------------
# Takes the new text from Azure OCR and splits into segments.
# Also uses regexs to capture entities.
# 
# Written primarily by Robbie thus far.
# -----------------------------------------------------------


# In[1]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
EXPORTDATADIR1 = ROUTETOROOTDIR + 'B_text_preproessing/csv_outputs/'
UTILDIR = ROUTETOROOTDIR + 'util'
JSONSDIR = ROUTETOROOTDIR + 'A_pdf_to_text/jsons_ke_gazettes/'


# In[3]:


import os
import re
import pandas as pd

os.chdir(IMPORTSCRIPTSDIR)
import orderingText
import setup


# In[4]:


def getNamesLRAstring(text):
    """Given the text of a segment, attempts to extract details such as name and address. 
    Regexs are targeted at Land Registration Act segments.
    
    args:
    text: string of text to extract entities from, typically a segment.
    
    returns: (name, address, land size, district, title number, 
    plot number , LR number, grant number, signator, signatorRole, 
    signator location, date, notice number, title of segment, subtitles of segment,
    MR number, act number, inner text (paragraphs after headers and before date). 
    
    Returns None for any entity not found, which is quite common among the
    later parts of the returns.
    """
    
    def extractName(string):
        """Extract the name being regerence in a segment such as THE LAND REGISTRATION ACT.
        
        example: WHEREAS (Robert Zakayo Muli), ..."""
        
        try:
            return re.search("WHEREAS (.*?),", string)[1]
        except:
            return None
    
            
    def extractAddress(string):
        """Extract the address in a segment following the structure of the LAND REGISTRATION ACT.
        
        example: WHEREAS Robert Zakayo Muli, of (P.O. Box 89452, Mombasa in the Republic of Kenya)..."""
        
        try:
            return re.search("WHEREAS .*?, of (.*?Kenya),", string)[1]
        except:
            try:
                return re.search("both of (P\.O\. .*?Kenya),", string)[1]
            except:
                try:
                    return re.search("all of (P\.O\. .*?Kenya),", string)[1]
                except:
                    return None
        
    def extractLandSize(string):
        """Extract the size of land in a segment following the structure of the LAND REGISTRATION ACT.
        
        example: ...land containing (1.05 hectares) or thereabout..."""
        
        try:
            return re.search("containing ?([0-9\.]+ hectare)", string)[1]
        except:
            return None
        
    def extractDistrict(string):
        """Extract the district and potentially region within the district 
        in a segment following the structure of the LAND REGISTRATION ACT. 
        
        example: ...situate in (north of Mtwapa Creek in Kilifi District), ..."""
        
        try:
            return re.search("situate in (.*?),", string)[1]
        except:
            return None
        
    def extractTitleNo(string):
        """Extract the title number of a registered piece of land 
        in a segment following the structure of the LAND REGISTRATION ACT.
        
        example: ...registered under title No. (Rongai/Rongai Block 1/1356), ..."""
        
        regex = r"(title No\. .*?),"
        try:
            return re.search(regex, string)[1]
        except:
            return None
        
    def extractPlotNo(string):
        """Extract the plot number of a registered piece of land
        in a segment following the structure of the LAND REGISTRATION ACT.
        
        example: ...known as (plot No. 11334/I/MN), situate ..."""
        
        try:
            return re.search("(plot No\. ?.*?),", string)[1]
        except:
            return None
        
    def extractLandRegistration(string):
        """Extract the land registration number of a piece of land
        in a segment following the structure of the LAND REGISTRATION ACT.
        
        example: ...piece of land known as (L.R. No. 9122/507), situate..."""
        
        try:
            return re.search(r"(L\.R\. No\. [0-9/]+)", string)[1]
        except: 
            return None
        
    def extractGrantNo(string):
        """Extract the grant number of a piece of land
        
        example: ... by virtue of a grant registered as (I.R. 55629/1), and ..."""
        
        try:
            return re.search("grant registered as (.*?),", string)[1]
        except:
            return None
        
    def extractGazetteNoticeNo(string):
        """Extract the gazette notice number from a segment.
        in a segment following the structure of the LAND REGISTRATION ACT.
        
        example: GAZETTE NOTICE NO. (2705)"""
        
        try:
            return re.search(r"GAZETTE NOTICE NO\. ([0-9]{4})", string)[1]
        except:
            return None
    
    def extractTitle(string):
        """Extract the title of a segment.
        
        example: (THE INTERGOVERNMENTAL RELATIONS ACT)"""
        
        try:
            return re.search(r"\n([ A-Z]+?) ?\n", string)[1]
        except:
            return None
    
    def extractSubtitles(string):
        """Extract the subtitles in a gazette.
        
        example: THE LAND REGISTRATION ACT \n (ISSUE OF A PROVISIONAL CERTIFICATE)"""
        
        try:
            return ",".join(re.findall(r"\n([ A-Z]+?) ?\n", string)[1:])
        except:  
            return None
    
    def extractDate(string):
        """Extract the date from the end of a gazette segment.
        
        example: (Dated the 24th March, 2017)"""
        try:
            return re.search("Dated the (.*?[0-9]{4})", string)[1]
        except:
            return None
    
    def extractSignator(string):
        """Extract the signator from the end of a gazette segment.
        
        example: (S. C. NJOROGE), \n Registrar of Titles, Nairobi"""
        
        try:
            return re.search(r"\n([\. A-Z']+), ?\n", string)[1]
        except:
            return None
    
    def extractSignatorLineRoleLocLine(string):
        """Get the last line from a segment that insn't all numbers. 
        Then clean this line to get rid of MR... phrase. Used as helper for below methods."""
        
        lastline = re.search(r"\n(.*)$", string)
        if lastline:
            lastline = lastline[1]
        else:
            return ""
        
        #the below is meant to catch the OCR from including a page number as the 
        #end of a segment
        if re.search(r"^[0-9 ]+$", lastline):
            lastline = re.search(r"\n(.*?)\n.*$", string)
            if lastline:
                lastline = lastline[1]
            else:
                return ""
            
            
        clean = lastline
        searchForMR = re.search(r"MR/[0-9]+", lastline)
        if searchForMR:
            span = searchForMR.span()
            clean = lastline[span[1]:]
        return clean
        
    
    def extractSignatorRole(string):
        """Extract the role of the signator from a segment.
        
        example: S. C. NJOROGE, \n (Registrar of Titles), Nairobi"""
        
        line = extractSignatorLineRoleLocLine(string)
        try:
            return re.search(r"(.*?),.*", line)[1]
        except:
            return None
    
    def extractSignatorLocation(string):
        """Extract the location of the signator from a segment.
        
        example: S. C. NJOROGE, \n Registrar of Titles, (Nairobi)"""
        
        line = extractSignatorLineRoleLocLine(string)
        try: 
            return re.search(r".*?, (.*?)\.", line)[1]
        except:
            return line
    
    def extractMRthing(string):
        """Extract interesting string beginning with MR appearing at the bottom of
        segments following the structure of the LAND REGISTRATION ACT.
        
        example: (MR/3123587)"""
        
        try:
            return re.search(r"MR/[0-9]+", string)[0]
        except:
            return None
        
    def extractActNo(string):
        """Extract string signifying year and number of act at top of segment,
        generally between title and subtitle.
        
        example: (No. 3 of 2012)"""
        
        try:
            return re.search(r"\n\(No\. [0-9]+ of [0-9]+ ?\) ?\n", string)[0]
        except:
            try:
                return re.search(r"\n\(Cap\. ?[0-9]+\) ?\n", string)[0]
            except:
                return None
            
    def extractInnerText(string, noToNumbers = True):
        """Extract the inner paragraph within most segments, generally beginning with
        'WHEREAS' or 'IT IS' or 'APPLICATION' or something similar.
        
        args:
        noToNumbers: If True, convert 'No.' (and similar) to 'numbers' within the text."""

        try:
            text = re.search(r"((WHEREAS|PURSUANT|TAKE NOTICE|IN PURSUANCE|IT IS) .*) Dated the", 
                             string, flags = re.DOTALL)[1] 
            if noToNumbers:
                return orderingText.convertNoToNumbers(text)
            else:
                return text
        except:
            return None
    
    textNoNewLines = text.replace("\n", "")
    
    return (extractName(textNoNewLines), extractAddress(textNoNewLines), extractLandSize(textNoNewLines), 
            extractDistrict(textNoNewLines), extractTitleNo(textNoNewLines), extractPlotNo(textNoNewLines), 
            extractLandRegistration(textNoNewLines), extractGrantNo(textNoNewLines),
            extractSignator(text), extractSignatorRole(text), extractSignatorLocation(text),
            extractDate(text), extractGazetteNoticeNo(text), extractTitle(text),
            extractSubtitles(text), extractMRthing(text), extractActNo(text), extractInnerText(textNoNewLines))


# In[5]:


class Segment(object):
    """Defines a single segment in the gazette."""
    
    def __init__(self, text):
        """Initiate a segment by loading in text. If the text is short enough and 
        is 'land-related' (has the word land within the text of the segment, 
        then use regexs to extract key feautres."""
        
        self.text = text
        self.landRelated = self.isLandRelated()
        self.isLRA = self.isLRAtest()
        self.shortEnough = self.isShortEnough()
        if self.landRelated and self.shortEnough:
            self.name, self.address, self.landSize, self.district, self.titleNo, self.plotNo, self.LR, self.grantNo, self.signator, self.signatorRole, self.signatorLocation, self.date,self.noticeNo, self.title, self.subtitles, self.MRNo, self.actNo, self.innerText = getNamesLRAstring(text)
    
    def isLRAtest(self):
        """Returns true if the segment contains the phrase 'THE LAND REGISTRATION ACT' """
        
        return "THE LAND REGISTRATION ACT" in self.text
    
    def isLandRelated(self):
        """Returns true if the segment contains the phrase 'land' """
        
        return "land" in self.text.lower()
    
    def isShortEnough(self):
        """Returns true if the text of a segment occurs on roughly one page or less."""
        
        return len(self.text) < 2000      # normally just over 2000 characters appear on a page
    
    def __str__(self):
        """Returns the whole text."""
        
        return self.text


# In[6]:


def allStartPoints(text):
    """Given a full page, determine the indices at which segments begin.
    
    args:
    text: full page of text from a gazette, or multiple pages concatenated.
    
    Returns:
    indices: indices in the string of the start of a segment."""
    
    pattern1 = r"GAZETTE NOTICE NO. [0-9]{3,5} *\n"    
    return [m.start(0) for m in re.finditer(pattern1, text)]

def getSegments(text, indices = None):
    """Given a full page of text, return a list of strings, each representing one segment.
    DO NOT actually return segment objects.
    
    args:
    text: text to parse for segments.
    indices: indices of segments to return. If None, will return all indices.
    
    returns: a list of segment text, or just a single segment text."""
    
    prevInd = 0
    ret = []
    startPoints = allStartPoints(text)
    for start in startPoints:
        if start-prevInd > 50:         # to get rid of segments which are clearly to short
            ret.append(Segment(text[prevInd:start]))
        prevInd = start
    if (len(startPoints)):
        segText = text[startPoints[len(startPoints) - 1]:]
        segment = Segment(segText)
        ret.append(segment)
    else:
        ret.append(Segment(text))
    if indices != None:
        return ret[indices]
    return ret


# In[7]:


def writeEntitiesToCsv(text, filename = "entities_test", filepath = "default",
                       includeNonLRA = False):
    """Write all regex-extracted entities found in each segment along with the segment text to a csv.
    Returns Pandas dataframe with same data as said csv.
    
    args: 
    text: raw text, typically from Read API, of any. amount of gazette.
    filenameArg: filename to write the csv to.
    filepath: filepath to write the csv to. If 'default', use EXPORTDATADIR.
    includeNonLRA: include segments whose header is not "THE LAND REGISTRATION ACT."
    
    returns: a pandas dataframe with regex-extracted entities by segment. 
        Will return 0 if no segments are found. Includes only segments that are land-related
        if includeNonLRA is true, and only segments with the header 'THELAND REGISTRATION ACT' 
        if includeNonLRA is false."""
    
    if filepath == "default":
        filepath = EXPORTDATADIR
    
    # column headers:
    lines = [["name", "address", "land size", "district", "title number", "plot number", "LR number", "grant number",
             "signator", "signator role", "signator location", "date", "notice number", "title",
             "subtitles", "MR number", "act number", "inner text", "text"]]
    segments = getSegments(text)
    for seg in segments:
        if seg.isLRA and seg.shortEnough:
            lines.append([seg.name, seg.address, 
                          seg.landSize, seg.district, seg.titleNo, seg.plotNo, seg.LR, seg.grantNo,
                          seg.signator, seg.signatorRole, seg.signatorLocation, seg.date,
                          seg.noticeNo, seg.title, seg.subtitles, seg.MRNo, seg.actNo, 
                          seg.innerText, seg.text])
        elif includeNonLRA and seg.shortEnough and seg.landRelated:
            lines.append([seg.name, seg.address, 
                          seg.landSize, seg.district, seg.titleNo, seg.plotNo, seg.LR, seg.grantNo,
                          seg.signator, seg.signatorRole, seg.signatorLocation, seg.date,
                          seg.noticeNo, seg.title, seg.subtitles, seg.MRNo, seg.actNo, 
                          seg.innerText, seg.text])
            
    if len(lines) == 1:
        # we didn't capture anything, don't bother writing the csv
        return 0
    setup.writeToCsv(filename, lines, filepath)
    df = pd.DataFrame(lines[1:], columns = lines[0])
    return df


# In[ ]:




