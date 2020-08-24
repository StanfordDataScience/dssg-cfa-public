# Building a Name Entity Recognition Model

This directory contains all the scripts and information necessary to train a spaCy NER model once pre-processed text and training data already exists. The model is then saved, and can be called easily. 

Code is split through several files, each of which has a more detailed description below:

* **A_train_modified_spacy_model_ipynb:** A step by step walkthrough of training a modified spaCy model using custom data. This process was mirrored using [this guide from the spaCy website under the section "Training an additional entity type"](https://spacy.io/usage/training) which gives an example of adding the label `ANIMAL` to the default spaCy model.

* **B_test_modified_spacy_model.ipynb:** A notebook that loads the trained model, runs through two sample tests, and outlines the shortcomings of the model and outlines next steps.

* **C_exportNERAPI**: A notebook that accesses the trained spaCy model. Run it on any entire (pre-processed) gazette. 

* **Z_general_spaCy_beginner_tutorial.ipynb:** A notebook that walks through accessing, using, and modifying spaCy for databases in English as well as in other languages(such as Portuguese).

## Getting Started

Start by training the modified model by walking through `A_train_modified_spacy_model_ipynb` notebook, then test the model by walking through the `B_test_modified_spacy_model.ipynb` notebook and export the entities to be converted to nodes and edges using the `C_exportNERAPI` notebook.


**Note** The notebook titled `A_train_modified_spacy_model_ipynb` notebook walks one through the steps of training a model. The output of these training steps, trained on 6286 Land Registration Act notices from 80 different gazettes published 2012 - 2019, is stored in the `model_outputs` file. These training notices are not uploaded to this GitHub repo due to their large size. However, a few samples are uploaded to guide the implementation of the training steps. We recommend the user to apply these steps on their training sets. 


### Skills Required

* The only skill required is operating `spaCy`. One can learn to operate spacy by following the `Y_general_spaCy_tutorial.ipynb` and reading through the spaCy website: https://spacy.io/api, which is well documented.

* The other skill required is a basic knowledge of python.

### Assumptions

Here are the overall assumptions made in this repo. The specific assumptions are stated in the notebooks.

* **Clean text**: the spaCy model training assumes that it is being trained on a clean text with no/minimal typos and no segmentation fault.

* **Short text**: the spaCy model is best equipped for relatively short segments that are usually one paragraph long (about 10 lines of text).

### FAQ:

* *How much training data is enough training data to have spaCy work effectively?* 

We don't have a full proof method of determining how much training data is sufficient. However, we have gained a promising model performance with as few as 20 notices/sections of the gazette. Our most up to date model, which lives in `model_outputs`, is trained on 6286 Land Registration Act notices.

* *How long does it take to retrain the spaCy model?*

Two parts of the training take long: extracting the default entities and training the model. In order to counteract the catastrophic forgetting problem described in the `A_train_modified_spacy_model_ipynb` notebook, the model needs to be trained on the default labels as well. Extracting these default entities for a large number of notices takes some time. For example, running this proceedure on the 6286 notices took close to four hours.

The other part that takes a while is training the model. Training the model on 6286 notices with 150 iterations took a little over four hours. In total, the current model in the `model_outputs` repo took eight(8) hours.


* *I see that the spaCy model is only trained on the Land Registration Act. How versatile is it?* 

Unfortunately, the current model in the `model_outputs` folder performs poorly on acts other than the Land Registration Act. It performs slightly better than the default spaCy model on some entities while it performs slightly worse on other entities. Overall, the current modified model's performance on acts other than the Land Registration Act is unrealiable.

* *What potential bottlenecks does the model have?*

*Labels*: When training the model, make sure all your modified labels are in the `modified_labels` list. For instance, if one wishes to extract the entity called 'ANIMAL', this label needs to be added to the `modified_labels` list.

*Packages*: When one is importing spaCy, also import the dependencies required. Since these dependencies depend on the user's local computer, we recommend reading through the error messages from the installation process and fixing them as needed.

### Future Directions

* Future directions have been outlined, in detail, under the Conclusion section in the `B_test_modified_spacy_model.ipynb` notebook.