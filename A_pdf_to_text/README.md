# PDF to text

This directory contains all of the scripts and information necessary to convert PDFs from the online Connected Africa and Gazeti.Africa databases to raw text. 

This involves: downloading the PDFs in bulk; sending the PDF data to Microsoft Cognitive Service's Read API and storing the result (there is also information about using Form Recognizer API to read tables); and translating this output into raw text. 

The code is split through several files, each of which has a more detailed description below:

* **1_jsons_from_pdfs.ipynb:** Calls scripts for getting all URLs of Kenya Gazette PDFs (for a chosen date range) from Connected Africa and Gazeti.Africa and sending these through our OCR Service, the Microsoft Cognitive Services Read API. 
    + This is in the form of a notebook because some manual monitoring of the process is recommended. Actually running each segment of the notebook will call scripts to perform the tasks for you.  

* **2_correct_database_errors.ipynb**: Detects and offers options for correcting misnamed Gazettes. 

* **3_get_tables.ipynb**: Getting OCR'd versions of tables and charts from Gazette pages that have them, appending the results to the existing JSON of the page (generated through the cheaper Read API). This can also be used to build a simpler and more efficient pipeline using just the Form Recognizer API. 

* **helpers** folder: files containing helper functions for the above processes (1, 2, and 3). These include: 
    + *write_urls*: All functions for getting PDF URLs from the database website. 
    + *json_extraction*: All functions for extracting JSONs using the Read API. 
    + *check_gazette_filenames*: All functions for checking the filenames of Gazette JSONs and renaming files accordingly. 
    + *dest_fn_from_url*: All functions for getting filenames from a URL and converting filenames between Gazeti's naming schema, Connected Africa's naming schema, and our naming schema (which is a combination of the first two). 

* **4_orderingText.ipynb:** Turns json output of Read API into raw text.

**Walkthroughs for use**: 

* **walkthrough_notebook.ipynb (or .html):** walks the user through the code in this directory which forms a sub-section of our overall pipeline. Includes intermediate outputs for the sake of clarity.

* **additional_walkthroughs** foder contains: 
    + *get_source_pdfs_walkthrough*: documentation of the process for getting PDFs from the Gazeti and Connected Africa APIs. (We had to do some reverse-engineering here, so we thought that this would be helpful for others working with these databases in the future.) 
    + *ocr_output_walkthrough*: an explanation of the output of the Read API and the Form Recognizer Layout API. This describes the JSON output, which we later convert into raw text.  


## Skills required

* Getting data from the Connected Africa and Gazeti websites required some familiarity with the Python requests package, as well as a willingness to use the websites' developer tools and generally navigate some trial and error. 

* Working with Read API outputs requires some experience working with nested data structures in Python. 

* All that is needed to understand the ordering of text is a bit of geometric sense and a very basic understanding of how the k-means algorithm works (for determining how many columns there are).

## Assumptions

* As reflected in the *get_source_pdfs_walkthrough* file in the *additional_walkthroughs* folder, we make some assumptions about how files are stored in the source databases. (Though, these assumptions are rooted in extensive work with the data.) In particular, we note that document ids are unique to a specific document and do not change; and checksums are unique to content and do not change. 

* As reflected in the *get_source_pdfs_walkthrough*, we followed a somewhat hacky and potentially inefficient pathway to accessing the data that we used. There may be an easier way to do all of this!

* We assume that the output of the Read API and our scripts for ordering text produce a nearly-perfect output for paragraph-form text, for one- and two-column pages. We base this on extensive work with the outputs. 

* When we began work with this project, we were given text generated through an open-source PDF-to-text tool, Tesseract. This original text output often did not recognize columns, reading across a page and thus generating text that was out of order. We assumed that this text was not workable for *extracting relationships*, a core goal of our work, since we could not distinguish Gazette Notices from each other (as described in part B of this repo). It is possible that there is a way to work with this open-source tool that we were not able to discover. 


## FAQ

* *Why does the orderingText.readPage() function return an empty string for an entire page, and not infrequently?* readPage is set by default to not even try to read pages that it detects has having more than two columns. It will just return an emtpy string every time this happens. This is done out of caution, and a wish to avoid adding bad or poorly read text at the expense of capturing every last scrap of gazette. This can easily be avoided by setting the readTables flag to be true, but we caution the reader that reading tables is not something readAPI does well.

## Future Directions

* *Incorporating Form Recognizer Layout API to read tables; knitting together those tables and storing them in the text output*: Significant data exists in the Gazettes that is stored in tables and charts, which we are currently not capturing effectively. We recommend using the Layout API either instead of the Read API, on all pages with more than two columns, or on all pages determined to be of interest (e.g., containing a keyword); then writing a script to translate the output into usable data. 

* *Get better data for more years*: We only processed the 2000-2019 Gazettes. 
