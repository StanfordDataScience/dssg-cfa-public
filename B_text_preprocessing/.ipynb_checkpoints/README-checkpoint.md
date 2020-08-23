# Text Pre-processing

This directory contains all of the scripts and information necessary to pre-process raw gazette before it is fed into out Named Entity Recogniton Tool, spaCy. This process includes segmenting raw text, extracting entities from these segments using regular expressions, and manipulating this data so that spaCy can work with it easilt. Scripts are currently optimized to work with gazette segments under the title "THE LAND REGISTRATION ACT."

Code is split through several files, each of which has a more detailed description below:

* **retoolingSegmentation.ipynb:** splits raw text into segments. Uses regular expressions to extract entities from those segments for the Land Registration Act. Write this information to csv.

* **readingJsonsBulk.ipynb:** makes bulk calls to retoolingSegmentation.py and 'A/orderingText.py'. Reads many gazette segments into csv form with entities extracted. 

* **trainingDataForSpaCy.ipynb:** converts pre-processed gazettes in csv format from readJsonsBulk into Python objects that are used by spaCy as training data. Does some pre-processing and regular expression entity extraction on top of what takes place in retoolingSegmentation.py.

* **walkthrough_notebook.ipynb (or .html):** walks the user through the code in this directory which forms a sub-section of our overall pipeline. Includes intermediate outputs for the sake of clarity.


## Skills required

The only skill which is slightly niche required to understand and extend the notebooks in this directory is a somewhat advanced understanding of regular expressions.

## Assumptions

This notebook was built with the gazette structure used between 2012 and 2020 in mind. If this changes, many of the regular expressions are likely to break.

## FAQ

* *Why is 'No.' (and similar phrases) sometimes converted to 'number' and sometimes not?* Our spaCy NER model performs much better when 'No.' is replaced by 'number' in its input. We discovered this after building a lot of reegular expressions to use as a baseline and to train the model. As a result, these scripts at times juggle two copies of the text: one that keeps 'No.,' so that regular expressions work properly, and one that switch to 'number,' so that spaCy can work properly. The biggest manifestation of this is that by default, the 'inner text' attribute a segment converts to 'number', while the 'text' attribute keeps 'No.'

* *How versatile are the regexs in these scripts?* Only moderately. Some stuff appears in every gazette (Date, signator, gazette notice number, title, etc.) The regexs to capture these things work quite well across a host of different segment styles. Every thing that is between the header and footer, however, changes a lot between gazettes. The regexs to capture this stuff in the middle is really only designed to work for the land registration act and will be erroneous in most other cases.

## Future Directions

* *Create regular expressions for different acts:* The work in this directory can be improved by adding regular expressions to capture entities in different acts other than the Land Registration Act. This is only worthwhile if used to improve the spaCy model, however, as regular expressions are not a long-term versatile solution. 
