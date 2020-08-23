# Network Building

This directory contains all of the scripts and information necessary to use the spaCy named entity recognition model we have built to create a network between individuals, organizations, and plots of land from Land Registration Act segments. This process includes create Python objects to act as data structures and symbollicaly define the objects within the network, and building an infrastructure of data structures to quickly add information to the network. 

Code is split through several files, each of which has a more detailed description below:

* **networkClasses.ipynb:** defines Python objects which make up the edges and nodes of our graph. Determines what information falls within each graph object. 

* **networkInfrastructure:** creates data structures which store all the information in out network. Quickly adds new data to the network, and converts the network from Python objects into a csv format usable by almost any network analysis software.

* **walkthrough_notebook.ipynb (or .html):** walks the user through the code in this directory which forms a sub-section of our overall pipeline. Includes intermediate outputs for the sake of clarity.


## Skills Required

* just basic Python


## FAQ

* *When adding a data point to the graph, when does the new entity (person, land, or org) get classified as the same as one currently in the graph and merged instead of having a whole new node created?* This question is one we hope that those who extend this code answer much more thoroughly than we do. Right now two person objects count as the same when they have the same name and ID (or both have no ID at all). Two organizations get classified as the same when they have the same name. Plots of land are never counted as the same (you should come up with better system. yes YOU!). 

* *What the heck is going on with those data structures in networkInfrastructure.ipynb?* A lot. They are in many respects built to be extended. When adding a new organization, we want to make sure that we merge with a previous organization with the same name if possible. This is why our data structure is a map with names as keys instead of a list or something similar: finding that org with the same name is O(1). We have done this same hashing structure but with a meaningless key for land and edges even though they we never check for duplicates in this category because we want to make it easy for the reader to extend this code by adding a more relevant hash key. 

## Future Directions

* *Incorporating with Aleph data schema:* While the Python objects in this directory were created to be somewhat in line with the Aleph data schema, they were also optimized for the type of data we extracted from land registration act segments. Incorporating this information into Aleph is essential in ensuring that the work done in this directory gets used in the field.