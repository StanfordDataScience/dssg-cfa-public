# Text Pre-processing

This directory contains all of the scripts and information necessary to pre-process raw gazette before it is fed into out Named Entity Recogniton Tool, spaCy. This process includes segmenting raw text, extracting entities from these segments using regular expressions, and manipulating this data so that spaCy can work with it easilt. Scripts are currently optimized to work with gazette segments under the title "THE LAND REGISTRATION ACT."

Code is split through several files, each of which has a more detailed description below:

* **retoolingSegmentation.ipynb:** splits raw text into segments. Uses regular expressions to extract entities from those segments for the Land Registration Act. Write this information to csv.

* **readingJsonsBulk.ipynb:** makes bulk calls to retoolingSegmentation.py and 'A/orderingText.py'. Reads many gazette segments into csv form with entities extracted. 

* **trainingDataForSpaCy.ipynb:** converts pre-processed gazettes in csv format from readJsonsBulk into Python objects that are used by spaCy as training data. Does some pre-processing and regular expression entity extraction on top of what takes place in retoolingSegmentation.py.

* **walkthrough_notebook.ipynb (or .html):** walks the user through the code in this directory which forms a sub-section of our overall pipeline. Includes intermediate outputs for the sake of clarity.
