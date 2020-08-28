### Data

You can find our date [here](https://drive.google.com/drive/u/0/folders/16_R47hapuC6afdi1ZHjYF87gtwf1Hdki) on Google Drive. This link should be active through at least 2021. 

The linked folder contains: 

1. The JSON outputs of our OCR process, for nearly all Gazettes 2000-2019. Note that there may be a few Gazettes that, due to the fact that they had incorrect filenames in the database, were mislabelled by our algorithm as duplicates and thus were not processed. We expect that this is at most 35 Gazettes, compared to the 2,000+ files that are here. 

2. The JSON outputs of the *first page* of every Gazette in the database labelled as published between 2000 and 2019, named with additional metadata. This was necessary for creating a mapping between our two databases; but we didn't want to OCR all of the Gazettes, because the Connected Africa database contained significant duplicates and we want the hash values for the same Gazettes to be the same. 

This (Github) folder contains: 

1. A mapping from the files in our DSSG-generated database (sometimes referred to as "curr_db") and the source databases (Connected Africa and Gazeti.Africa). 

2. Helper functions for accessing this mapping between databases exist in the `helpers` folder. 