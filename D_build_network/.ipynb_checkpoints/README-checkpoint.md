# Network Building

This directory contains all of the scripts and information necessary to use the spaCy named entity recognition model we have built to create a network between individuals, organizations, and plots of land from Land Registration Act segments. This process includes create Python objects to act as data structures and symbollicaly define the objects within the network, and building an infrastructure of data structures to quickly add information to the network. 

Code is split through several files, each of which has a more detailed description below:

* **networkClasses.ipynb:** defines Python objects which make up the edges and nodes of our graph. Determines what information falls within each graph object. 

* **networkInfrastructure:** creates data structures which store all the information in out network. Quickly adds new data to the network, and converts the network from Python objects into a csv format usable by almost any network analysis software.

* **walkthrough_notebook.ipynb (or .html):** walks the user through the code in this directory which forms a sub-section of our overall pipeline. Includes intermediate outputs for the sake of clarity.