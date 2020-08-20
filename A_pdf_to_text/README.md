# PDF to text

This directory contains all of the scripts and information necessary to download a PDF from one of Code for Africa's databases, call Read API on that PDF, and translate Read API's output into raw text. An example of this process is illustrated in walkthough_notebook.ipynb. 

Code is split through several files, each of which has a more detailed description below:

* **1_jsons_from_pdfs.ipynb:** A walk-through for pulling all URLs of Kenya Gazette PDFs (for a chosen date range) from Connected Africa and Gazeti.Africa and sending these through our OCR Service, the Microsoft Cognitive Services Read API, to get the json output. 

* **1b_correct_database_errors.ipynb**: A walk-through for pulling 

* **1c_get_tables.ipynb**: Getting OCR'd versions of tables and charts from Gazette pages that have them, appending the results to the existing JSON of the page (generated through the cheaper Read API). This can also be used to build a simpler and more efficient pipeline using just the Form Recognizer API. 

* **orderingText.ipynb:** Turns json output of Read API into raw text.

* **walkthrough_notebook.ipynb (or .html):** walks the user through the code in this directory which forms a sub-section of our overall pipeline. Includes intermediate outputs for the sake of clarity.