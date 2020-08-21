# dssg-cfa-public

## introduction

This Github directory was completed by the Code for Africa Team as part of Stanford's Data Science for Social Good program in the Summer of 2020. The end goal of our project is to create high quality and easily accessible relations datasets concerning land-related information from the Kenya Gazettes, aiming to help journalists uncover land corruption and protect natural resources.

Our outputs are: 
* A dataset of higher quality PDF-to-text translations of Kenya Gazettes.
* A beginning dataset of entities extracted from 2000-2019 land records (names, addresses, land plots, etc.), stored in a data schema comparable to that already implemented within Aleph, CfA’s data journalism platform. 
* A network of these entities. 


## directories

Each directory in this folder handles one portion of our pipeline. Within each directory is another readme file with further information on code in the directory. 

The vast majority of our code is written in jupyter notebook files for ease of annotation, visualization, and debugging. In order to call functions in one notebook from another, almost all of our notebooks have been converted to .py format. These .py versions are all stored in the directory 'util/py_files.' If you modify a notebook and would like the changes to a function to take effect within another script, the function convertAll() within the file setup.ipynb (or setup.py) in the util folder will reconvert all notebooks to .py format.

A high-level overview of the processes completed in each directory is as follows:

* **A_pdf_to_text:** Craft API calls to websites containing the Kenya Gazettes. Use Microsoft Cognitive Services' Read API on these PDFs. Finally, json output of Read API into ordered text.

* **B_text_preprocessing:** Extract separate segments from ordered text. Use regular expressions as a baseline for entity extraction.

* **C_build_ner_model:** Build a spaCy model to extract entities more accurately. 

* **D_build_network:** Useing our spaCy model, extract entities for a number of gazettes. Combine these entities into objects, and these objects into a network. Visualize the network and perform exploratory data analysis.

* **util:** Helpful scripts used throught the project and supplementary dataset.

## authors

Fellows in charge of the project were Tsion (T) Tesfaye, Thea Rossman, and Robert (Robbie) Thompson.

## acknowledgements

We would like to thank our partners, the Code for Africa project and the World Resources Institute, for their guidance and for bringing us this project. We would also like to thank our technical mentors and faculty advisors for their constant support.

