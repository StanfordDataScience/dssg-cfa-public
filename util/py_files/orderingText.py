#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -----------------------------------------------------------
# Put all of these various lines and words in the order
# that they appear in within the gazette
#
# Written primarily by Robbie (thus far)
# -----------------------------------------------------------


# In[2]:


# for others to use this script, it will help to change this variable to
# whatever the route it to the root of your dssg-cfa folder.
ROUTETOROOTDIR = '/home/dssg-cfa/notebooks/dssg-cfa-public/'
IMPORTSCRIPTSDIR = ROUTETOROOTDIR + "util/py_files"
EXPORTDATADIR1 = ROUTETOROOTDIR + 'B_text_preproessing/csv_outputs/'
UTILDIR = ROUTETOROOTDIR + 'util'
JSONSDIR = ROUTETOROOTDIR + 'A_pdf_to_text/jsons_ke_gazettes/'
TEXTDIR = ROUTETOROOTDIR + 'A_pdf_to_text/all_txt_files/'
import os
import json 
import matplotlib.pyplot as plt
import random
import numpy as np
from sklearn.cluster import KMeans

os.chdir(IMPORTSCRIPTSDIR)
import setup


# In[3]:


def readJsonIntoDict(filepath, filename, pageNum = 'all'):
    """Read a json from Read API into a Python dictionary and return it.
    
    args:
    filepath: directory to search for the gazette in.
    filename: name of json we are loading into Python format.
    pageNum: page number of gazette to read in.
        If pageNum == 'all', then return all pages.
        
    returns: A highly nested Python dictionary from Read API's json output.
    To understand the structure of this dictionary better, see Microsoft's help pages."""
    
    os.chdir(filepath)
    with open(filename) as json_file:
        data = json.load(json_file)
    pages_list = data['analyzeResult']['readResults']
    if pageNum == 'all':
        return pages_list
    else:
        return pages_list[pageNum]['lines']


colDict = {0:'r',1:'b',2:'g', 3: 'c', 4: 'm', 5: 'y'}
def genRandomColor():
    """Generate a random string which corresponds to a color in pyplot."""
    
    return colDict[random.randint(0,5)]
    

def plotLineBetweenTwoPoints(p1, p2, color = "b"):
    """Plot a line between p1 and p2.
    
    args:
    p1: A point in R2 (two dimensional space).
    p2: Another point in R2 (two dimensional space).
    color: A character which represents a color in pyplot.
        We will draw the line in this color."""
    
    xvals = (p1[0], p2[0])
    yvals = (p1[1], p2[1])
    plt.plot(xvals, yvals, color, linewidth = 0.3)
    
def drawBoundingBoxes(page_lines, color = 'b'):
    """Plot bounding boxes of all the lines that Read API finds. 
    This method is designed to be illustrative, showing the performance of Read API.
    
    page_lines: json dict for a single page which is the output of Read API.
    color: color to plot the bounding boxes in. If color is set to 'random', 
        then boxes will be assigned one of seven colors randomly and independently."""
    
    plt.figure(dpi = 200)
    bounding_boxes = [line['boundingBox'] for line in page_lines]
    for box in bounding_boxes:
        p1 = (box[0], -box[1])    # negative y coord because pyplot wants to draw from bottom right
        p2 = (box[2], -box[3])    # and Azure measures from top right
        p3 = (box[4], -box[5])
        p4 = (box[6], -box[7])
        if color == 'random':
            curCol = genRandomColor()
        else:
            curCol = color
        plotLineBetweenTwoPoints(p1,p2, curCol)
        plotLineBetweenTwoPoints(p2,p3, curCol)
        plotLineBetweenTwoPoints(p3,p4, curCol)
        plotLineBetweenTwoPoints(p1,p4, curCol)


# In[4]:


def getPageNumHeaderAndDate(topLeftXs, topLeftYs, page_lines):
    """Get indices of bounding boxes which correspond to to the header, page number, and date
    at the very top of the gazette page. 

    returns: (index of page num, index of overall header, index of date,
    text of page num, text of overall header, text of date)."""
    
    highestIndices = topLeftYs.argsort()[-3:]
    xvals = topLeftXs[highestIndices]
    pageNumOpts = np.where(topLeftXs == min(xvals))
    pageNumI = int(np.intersect1d(pageNumOpts, highestIndices))
    dateOpts = np.where(topLeftXs == max(xvals))
    dateI = int(np.intersect1d(dateOpts, highestIndices))
    headerI = int(np.setdiff1d(highestIndices, [dateI, pageNumI]))
    
    # these names are a bit of misnomers: pageNum and date are switched on every other page.
    pageNum = page_lines[pageNumI]['text']    
    header = page_lines[headerI]['text']
    date = page_lines[dateI]['text']
    
    return (pageNumI, headerI, dateI, pageNum, header, date)

def pageReadingPreAnalysis(page_lines):
    """Pre-processes the list of lines of a text to return a six-tuple of data.
    
    args:
    page_lines: json dict for a single page which is the output of Read API.
    
    numBoxes: the number of boxes on the page.
    topLeftXs: a numpy array of the x coordinate of the top left of each bounding box.
    topLeftYs: a numpy array of the y coordinate of the top left of each bounding box.
    boundingBoxes: a list of the bounding boxes of each line
    textArr: 
    topRightXs: """
    
    numBoxes = len(page_lines)
    boundingBoxes = [line['boundingBox'] for line in page_lines]
    topLeftXs = np.array([box[0] for box in boundingBoxes])      # for the sake of visualization
    topLeftYs = np.array([-box[1] for box in boundingBoxes])     # I'm going to keep using the negative y convention
    
    textArr = np.array([line['text'] for line in page_lines])
    return(numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr)


# In[5]:


def getNumCols(page_lines, numTrials = 4):
    """Attempt to determine the number of columns in a page."""
    
    ret = ""
    numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr = pageReadingPreAnalysis(page_lines)
    pageNumI, headerI, dateI, pageNum, header, date = getPageNumHeaderAndDate(topLeftXs, topLeftYs, page_lines)
    usedI = [pageNumI, headerI, dateI]
    remainingIndices = np.setdiff1d(range(numBoxes), usedI)
    remainingLeftXs = topLeftXs[remainingIndices]
    dataForKmeans = remainingLeftXs.reshape(-1,1)
    
    guesses = []
    for i in range(numTrials):
        last = 10 ** 5
        initialInertia = 0
        for i in range(2,10):
            kmeans = KMeans(n_clusters = i).fit(dataForKmeans)
            diffFromLast = last - kmeans.inertia_
            last = kmeans.inertia_
            if i == 2:
                initialInertia = kmeans.inertia_
            if kmeans.inertia_ < 100 and i == 2:       # 100 is a magic number found via tinkering
                guesses.append(2)
                break
            if (diffFromLast < initialInertia / 100):   # 100 is a magic number found via tinkering
                guesses.append(i-1)
                break
    if len(guesses) == 0:
        return None
    return round(sum(guesses) / len(guesses))
        


# Right now we are hopeless on seven-columned data entries. 

# In[6]:


def readIntoCsvLinesFormat(page_lines, numCols):
    """Attempt to read a page in order using a naive method: just reading across the page.
    
    Should hopefully give us something work with when we get to tables."""
    
    def whichCol(leftX, centers):
        return np.argmin(abs(centers - leftX))
    
    def getIndexAndValueOfTopOfCol(col, colVals, used, topLeftYs):
        badOnesEliminated = np.where(colVals == col, topLeftYs, -999) # -999 is a magic number meant to be super low
        badOnesEliminated = np.where(used, -999, badOnesEliminated)
        return (np.argmax(badOnesEliminated), np.max(badOnesEliminated))
    
    def isClose(distPerLine, maxY, curY):
        return maxY - curY < distPerLine / 3     # 3 is a magic number
        
    
    ret = ""
    numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr = pageReadingPreAnalysis(page_lines)
    pageNumI, headerI, dateI, pageNum, header, date = getPageNumHeaderAndDate(topLeftXs, topLeftYs, page_lines)
    usedI = [pageNumI, headerI, dateI]
    remainingIndices = np.setdiff1d(range(numBoxes), usedI)
    remainingLeftXs = topLeftXs[remainingIndices]
    remainingLeftYs = topLeftYs[remainingIndices]          # I really should find a way to put this beginning
    dataForKmeans = remainingLeftXs.reshape(-1,1)          # piece into it's own method
    
    #use kmeans to find where each column starts
    kmeans = KMeans(n_clusters = numCols).fit(dataForKmeans)
    centers = kmeans.cluster_centers_.flatten()
    centers.sort()
    
    approxNumCols = (numBoxes - 3) / numCols
    totalDist = abs(max(remainingLeftYs) - min (remainingLeftYs))
    distPerLine = totalDist / approxNumCols
    
    used = np.zeros(numBoxes, dtype = np.bool_)
    used[usedI] = True

    colVals = np.array([whichCol(leftX, centers) for leftX in  topLeftXs])
    for i in usedI:
        colVals[i] = -1
    
    lines = []
    while (used == False).any():
        indicesAndValues = [getIndexAndValueOfTopOfCol(col, colVals, used, topLeftYs) for col in range(numCols)]
        indices = [a[0] for a in indicesAndValues]
        values = [a[1] for a in indicesAndValues]
        maxY = max(values)
        line = []
        for i in range(numCols):
            if isClose(distPerLine, maxY, values[i]):
                line.append(page_lines[indices[i]]['text'])
                used[indices[i]] = True
            else:
                line.append('')
        lines.append(line)
    return lines


# In[7]:


def getTopIndicesAccountingForMask(topLeftYs, mask):
    """Return the highest value in topLeftYs whose index is also True in mask."""
    
    badRm = np.where(mask, topLeftYs, -999)
    return np.argsort(-badRm)

def isClose(curTopI, nextTopI, topLeftYs, cutoff = 0.05):
    """Returns true if the vaue in topLeftYs at index curTopI is almost the same as at index nextTopI (within cutoff)."""
    
    return abs(topLeftYs[curTopI] - topLeftYs[nextTopI]) < cutoff

def getAllLineIndices(topLeftYs, mask):
    """Returns the indices of topLeftYs from highest to lowest in the form of a jagged array (made of lists).
    All entries that are very close are in the same sublist within the outer returned list."""
    
    ret = []
    topIs = getTopIndicesAccountingForMask(topLeftYs, mask)
    numEntries = len(topLeftYs)
    i = 0
    curTopI = topIs[i]
    while mask[curTopI]:
        curTopI = topIs[i]
        if i >= numEntries - 1:
            ret.append([curTopI])
            return ret
        nextTopI = topIs[i+1]
        thisLine = [curTopI]
        while isClose(curTopI, nextTopI, topLeftYs) and mask[nextTopI]:
            thisLine.append(nextTopI)
            i += 1
            if i >= numEntries - 1:
                break
            curTopI = topIs[i]
            nextTopI = topIs[i+1]
        ret.append(thisLine)
        i += 1
        if i >= numEntries:
            break
        curTopI = topIs[i]
    return ret

def getText(jaggedArray, textArray, topLeftXs, sep = ' ', noNewLineLines = None):
    """From a jagged array of 2d lists, each containing indices of entries
    which belong on a line together, print """
    
    # deal with adding newlines at the end of each line or not
    if not np.any(noNewLineLines):
        noNewLineLines = np.zeros(len(topLeftXs))
        
    ret = ''
    lenArr = len(textArray)
    lineNum = 0
    
    #for each list of indices that represents one line
    for line in jaggedArray:
        mask = np.zeros(lenArr, dtype = np.bool_)      # True only for the indices of this line
        mask[line] = True
        order = getTopIndicesAccountingForMask(-topLeftXs, mask)     # starts with the beginning of this line
        i = 0
        nextI = order[i]         # next index to add to ret
        while mask[nextI]:
            ret += textArray[nextI] + sep
            i += 1
            lastI = nextI
            nextI = order[i]
        if not noNewLineLines[lastI]:
            ret += "\n"
        elif ret[-1] == "-":
            ret = ret[:-1]
        lineNum += 1
    return ret


# In[8]:


def isLeftColumn(box, midPage = 4.2):     # 4.2 is a magic number
    """Returns true if a bounding box is entirely on the left side of a page, false otherwise."""
    
    rightSide = box[2]
    return rightSide < midPage

def isRightColumn(box, midPage = 3.8):     # 3.8 is a magic number
    """Returns true if a bounding box is entirely on the right side of a page, false otherwise."""
    
    leftSide = box[0]
    return leftSide > midPage

def readTitlePage(page_lines):
    """Takes in the lines from a title page (first in the gazette) and returns the text in order.
    Sort of works well enough for now, need to write some more general methods."""
    
    def isMiddleColumnText(text):
        """Determines if text is commonly found right in the middle of the gazette on title page."""
        
        if text == "THE KENYA GAZETTE":
            return True
        if text == "Publiished by Authority of the Republic of Kenya":
            return True
        if text == "(Registered as a Newspaper at the G.P.O.)":
            return True
        if text[0:7] == "NAIROBI":
            return True
        if text[0:8] == "Price Sh.":
            return True
        if text[0:4] == "Vol.":
            return True
        return False
        

    def isSpecialTopText(text):
        """Returns true if the text found often appears off-center at the top of a gazette.
        Examples include 'SPECIAL ISSUE' and 'NATIONAL COUNCIL FOR LAW REPORTING LIBRARY.' """
        
        if text == "SPECIAL ISSUE":
            return True
        if text in 'NATIONAL COUNCIL FOR LAW REPORTING LIBRARY':
            return True
        if text in 'HARAMBEE' or text in 'ABEE':
            return True
        return False
    
    jaggedLinesArray = []
    numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr = pageReadingPreAnalysis(page_lines)
    
    specialtxtMask = np.array([isSpecialTopText(text) for text in textArr])
    unused = specialtxtMask == False
    jaggedLinesArray += getAllLineIndices(topLeftYs, specialtxtMask)
    

    middlecolMask = np.array([isMiddleColumnText(text) for text in textArr])
    middlecolMask = np.logical_and(middlecolMask, unused)
    unused = middlecolMask == False
    jaggedLinesArray += getAllLineIndices(topLeftYs, middlecolMask)
    
    
    leftcolMask = np.array([isLeftColumn(box) for box in boundingBoxes])
    leftcolMask = np.logical_and(leftcolMask, unused)
    unused = leftcolMask == False
    jaggedLinesArray += getAllLineIndices(topLeftYs, leftcolMask)
    
    
    rightcolMask = np.array([isRightColumn(box) for box in boundingBoxes])
    rightcolMask = np.logical_and(rightcolMask, unused)
    jaggedLinesArray += getAllLineIndices(topLeftYs, rightcolMask)
    
    return getText(jaggedLinesArray, textArr, topLeftXs)


# In[9]:


def readTablePage(page_lines):
    """Meant to a read a page from right to left and then up to down like a normal paragraph. 
    Doesn't work too hot on tables."""
    
    jaggedLinesArray = []
    numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr = pageReadingPreAnalysis(page_lines)
    pageNumI, headerI, dateI, pageNum, header, date = getPageNumHeaderAndDate(topLeftXs, topLeftYs, page_lines)
    jaggedLinesArray.append([pageNumI, headerI, dateI])
    usedI = [pageNumI, headerI, dateI]
    unused = np.ones(numBoxes, dtype = np.bool_)
    unused[usedI] = False
    
    jaggedLinesArray += getAllLineIndices(topLeftYs, unused)
    return getText(jaggedLinesArray, textArr, topLeftXs, sep = ',')


# In[ ]:





# In[10]:


def convertNoToNumbers(text):
    text = text.replace("No.", "number")
    text = text.replace("NO.", "number")
    text = text.replace("Nos.", "numbers")
    text = text.replace("NOs.", "numbers")
    return text


# In[11]:


def getRightBorders(page_lines):
    """Get the points in inches where bounding boxes tend to end (on the right side).
    Used for determining the shapes of paragraphs."""
    
    numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr = pageReadingPreAnalysis(page_lines)
    topRightXs = np.array([box[2] for box in boundingBoxes]) 
    dataForKmeans = topRightXs.reshape(-1,1)
    
    #use kmeans to find out where boxes tend to end
    kmeans = KMeans(n_clusters = 6).fit(dataForKmeans)       # 6 is a magic number
    centers = kmeans.cluster_centers_.flatten()
    labels = kmeans.labels_
    pointsPerCenter = [sum(i == labels) for i in range(6)]       # 6 is (still) a magic number
    biggestCenterIndices = np.argsort(pointsPerCenter)[-2:]
    rightBorders = centers[biggestCenterIndices]
    rightBorders.sort()
    return rightBorders


# In[12]:


def midParagraph(topRightXs, midPage = 3.95, rightEdge = 7.45):
    """Returns a mask: true if the given bounding box is in the middle of a paragraph, false otherwise."""
    
    # 3.95 and 7.44 are (somewhat) magical numbers, to see where they are derived call observeRightBorder()
    maxDist = 0.1    # maximum distance from the end of this column
    
    #long form:
    #isLeftColEndParagraph = np.logical_and(midPage - topRightXs < 0.2, midPage - topRightXs > 0)
    
    #short form:
    isLeftColEndParagraph = abs(midPage - topRightXs - 0.1) <= 0.1
    isRightColEndParagraph = abs(rightEdge - topRightXs - 0.1) <= 0.1
    
    return np.logical_or(isLeftColEndParagraph, isRightColEndParagraph)

#test = np.array([3.95, 4.1, 3.96, 3.97, 12, 7, 7.43, 7.46, 7.49, 7.5])
#midParagraph(test)


# In[13]:


def read2ColPagePreserveParagraphs(page_lines, keepPageHeader = False):
    """Reads your standard gazette two-column page in order."""
    
    jaggedLinesArray = []
    numBoxes, topLeftXs, topLeftYs, boundingBoxes, textArr = pageReadingPreAnalysis(page_lines)
    pageNumI, headerI, dateI, pageNum, header, date = getPageNumHeaderAndDate(topLeftXs, topLeftYs, page_lines)
    topRightXs = np.array([box[2] for box in boundingBoxes]) 
    if keepPageHeader:
        jaggedLinesArray.append([pageNumI, headerI, dateI])
    usedI = [pageNumI, headerI, dateI]
    unused = np.ones(numBoxes, dtype = np.bool_)
    unused[usedI] = False
    
    midPage = findMiddleOfPage(topLeftXs, topRightXs)
    leftcolMask = np.array([isLeftColumn(box, midPage) for box in boundingBoxes])
    leftcolMask = np.logical_and(leftcolMask, unused)
    unused = leftcolMask == False
    jaggedLinesArray += getAllLineIndices(topLeftYs, leftcolMask)
    
    rightcolMask = np.array([isRightColumn(box, midPage) for box in boundingBoxes])
    rightcolMask = np.logical_and(rightcolMask, unused)
    jaggedLinesArray += getAllLineIndices(topLeftYs, rightcolMask)
    
    rightEdge = findRightEdgeOfPage(topRightXs)
    midParagraphNoNewLines = midParagraph(topRightXs, midPage, rightEdge)
    
    return getText(jaggedLinesArray, textArr, topLeftXs, noNewLineLines = midParagraphNoNewLines)


# In[14]:


def findMiddleOfPage(topLeftXs, topRightXs):
    """Find the x coordinate of a page so that if we draw a vertical line there,
    it intersects the fewest bounding boxes of our OCR output. Vertical line must also be
    close to the middle of the page (between 2 and 6 inches from the left border). Once a
    suitable x coordinate is found (at most 1 intersection), we try to push it left as far as we can.
    
    args: 
    topLeftXs: vector of left endpoints of bounding boxes.
    topRightXs: vector of right endpoints of bounding boxes.
    
    returns: best (or tied for best) x coord to divide the boxes."""
    
    curXCoord = 4
    bestXCoord = 4
    checkAboveNext = True
    curNumSteps = 0
    increment = 0.05
    fewestNumIntersecting = len(topLeftXs)
    while curNumSteps < 40:
        curNumIntersecting = numIntersecting(topLeftXs, topRightXs, curXCoord)
        if curNumIntersecting == 1:
            
            #if we are to the right of center, take what we have.
            if checkAboveNext and curXCoord != 4:
                return curXCoord
            
            #if we are to the left of center, try to keep moving left.
            else:
                while curNumIntersecting < 2:
                    curXCoord -= increment
                    curNumIntersecting = numIntersecting(topLeftXs, topRightXs, curXCoord)
                return curXCoord + increment
                
                
        if curNumIntersecting < fewestNumIntersecting:
            bestXCoord = curXCoord
            fewestNumIntersecting = curNumIntersecting
        checkAboveNext = not checkAboveNext
        if checkAboveNext:
            curNumSteps += 1
        curXCoord = 4 + (2 * checkAboveNext - 1) * increment * curNumSteps
    return bestXCoord

def findRightEdgeOfPage(topRightXs):
    """Find the lowest x coordinate of a page so that if we draw a vertical line there,
    it intersects the no bounding boxes of our OCR output.
    
    args: 
    topLeftXs: vector of left endpoints of bounding boxes.
    topRightXs: vector of right endpoints of bounding boxes.
    
    returns: lowest x coord which intersects no boxes."""
    
    curXCoord = 6.5    # 6.5 designed to almost never be all the way to the right
    bestXCoord = 6.5 
    curNumSteps = 0
    increment = 0.05
    while curNumSteps < 60:
        curNumIntersecting = sum(topRightXs >= curXCoord)
        if curNumIntersecting == 0:
            return curXCoord
        curNumSteps += 1
        curXCoord = 6.5 + increment * curNumSteps
    return curXCoord
    
def numIntersecting(topLeftXs, topRightXs, xCoord):
    """Find the number of 1D line segments drawn between topLeftXs and topRightXs which contain xCoord.
    Used to find a line dividing the two columns of a page and see if it intersects many lines.
    
    args:
    topLeftXs: vector of left endpoints of line segments.
    topRightXs: vector of right endpoints of line segments.
    xCoord: point which we are checking to see if the segments contain. 
    
    returns: the number of segments containing xCoord."""
    
    return sum(np.logical_and(topLeftXs <= xCoord, topRightXs >= xCoord))


# In[15]:


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
    
    page_lines = jsonDict[pageNum]['lines']
    if len(page_lines) < 20:
        # not enough lines on this page, don't bother with it.
        return ''
    if pageNum == 0:
        text = readTitlePage(page_lines)
    else:
        numCols = getNumCols(page_lines)
        if numCols == None or numCols > 2:
            if includeTables:
                text = readTablePage(page_lines)
            else:
                return ''
        else:
            text = read2ColPagePreserveParagraphs(page_lines, keepPageHeader)
    for fn in cleaningFns:
        text = fn(text)
    return text


# In[18]:


def convertAllJsonsToTxt(inputDir = JSONSDIR, outputDir = TEXTDIR, includeTables = False):
    """Convert every page from every json in inputDir into a txt file in outputDir.
    
    args:
    inputDir: directory to read jsons in from.
    outputDir: directory to write txts to.
    includeTables: if True, include the transcription of pages which look like tables (>2 columns).
         Otherwise, write an empty txt for table pages."""
    
    os.chdir(inputDir)
    jsonNames = get_ipython().getoutput('ls')
    for jsonName in jsonNames:
        jsonDict = readJsonIntoDict(inputDir, jsonName)
        numPages = len(jsonDict)
        for pageNum in range(0, numPages):
            pageText = readPage(jsonDict, pageNum, keepPageHeader = True, includeTables = includeTables)
            filename = jsonName + "-page-" + str(pageNum + 1)
            setup.writeTxt(filename, pageText.encode('utf-8'), ROUTETOROOTDIR)            


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




