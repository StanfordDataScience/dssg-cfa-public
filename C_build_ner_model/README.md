# Building a Name Entity Recognition Model

This directory contains all the scripts and information necessary to train a spaCy NER model once pre-processed text and training data already exists. The model is then saved, and can be called easily. 

Code is split through several files, each of which has a more detailed description below:

* **A_train_modified_spacy_model_ipynb:** A step by step walkthrough of training a modified spaCy model using custom data. This process was mirrored using [this guide from the spaCy website under the section "Training an additional entity type"](https://spacy.io/usage/training) which gives an example of adding the label `ANIMAL` to the default spaCy model.

* **B_test_modified_spacy_model.ipynb:** A notebook that loads the trained model, runs through two sample tests, and outlines the shortcomings of the model and outlines next steps.

* **C_exportNERAPI**: A notebook that accesses the trained spaCy model. Run it on any entire (pre-processed) gazette. 

* **Z_general_spaCy_beginner_tutorial.ipynb:** A notebook that walks through accessing, using, and modifying spaCy for databases in English as well as in other languages(such as Portuguese).