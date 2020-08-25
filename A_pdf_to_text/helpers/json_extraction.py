#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
Helper functions to call the Microsoft Cognitive Services APIs to get and 
save OCR'd JSON outputs of one or multiple files. 
'''

import json
import sys
import requests
import time
import os
import PyPDF2
import io
import re

from helpers import dest_fn_from_url as df

# 17 inches (max for Read API) x 72 points per inch
MAX_DIM = 17*72

# rigorously commented for clarity


# In[ ]:


def call_read_api(final_dest_url = "", flag = "url", image_path = ""):
    '''    
    Function to call Microsoft cognitive services Read API on a single gazette (all pages).
    
    Flag should be "url" or "pdf". 
    If pdf, provide path to the PDF file. 
    If URL, provide url which points to the PDF file (does not redirect).

    Returns: 
    1. JSON-formatted output of the analysis
    2. Boolean for whether the analysis was successful
    (If analysis was unsuccessful, the output of the analysis returned will be JSON-formatted
    and include the text of the error message)
    '''

    # unique to our Computer Vision resource ("keys and endpoints" tab)
    endpoint = "<YOUR ENDPOINT HERE>"
    subscription_key = "<YOUR SUBSCRIPTION KEY HERE>"

    text_recognition_url = endpoint + "/vision/v3.0/read/analyze"

    # ---------------------
    # Extracting text requires two API calls: One call to submit the
    # image for processing, the other to retrieve the text found in the image. 
    # ---------------------
    
    # ------ FIRST API CALL: SUBMIT THE IMAGE ------ 
    
    # content-type is the type of data sent to the API (octet-stream for bytes; json for url)
    
    if flag == "url":
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': subscription_key
        }

        # posts request to the text_recognition_url (sending data to server)
        response = requests.post(text_recognition_url, headers=headers, json={'url': final_dest_url})
        
    elif flag == "pdf": 
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/octet-stream'
        }

        pdf_data = open(image_path, 'rb').read()
        response = requests.post(text_recognition_url, headers=headers, data=pdf_data)
        
    else: 
        return "Bad flag; should be \'pdf\' or \'url\'", False 
    
    # Return false if call did not go through 
    if response.status_code != 202: 
        msg = "Bad request URL/PDF for " + final_dest_url
        return msg, False


    # ------ SECOND API CALL: RETRIEVE THE TEXT FROM THE SERVER ------ 
    
    # (Our request returns a response object, which has information)
    # The response object contains the URL used to retrieve the recognized text.
    # This is the URL where our recognized text is currently "stored" on Microsoft's end
    operation_url = response.headers["Operation-Location"]

    # The recognized text isn't immediately available, so poll to wait for completion.
    analysis = {}
    poll = True
    while (poll):
        # (GET request means that we're getting data from a server)
        # Same headers as before -- our credentials & we want the output in JSON 
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        # store the JSON format response in analysis 
        analysis = response_final.json()

        # when complete, the analysis object will have an "analyzeResult" element
        if ("analyzeResult" in analysis):
            poll = False
        
        # if the analysis failed 
        if ("status" in analysis and analysis['status'] == 'failed'):
            return analysis, False 
        if ("error" in analysis):
            return analysis, False
        
        # limit calls to our subscription data rate (10 calls per second)
        time.sleep(0.1)
         
    return analysis, True


# In[ ]:


def add_page(reader, i, writer): 
    '''
    Add page at index i (starting at 0) from PDFreader to PDFwriter object.
    '''
    page = reader.getPage(i)
    width = float(page.mediaBox.lowerRight[0]) 
    height = float(page.mediaBox.upperLeft[1]) 
    # resize if width or height of page is too large
    if width > MAX_DIM: 
        width = MAX_DIM
        page.scaleTo(MAX_DIM, height)
    if height > MAX_DIM: 
        page.scaleTo(width, MAX_DIM)
    writer.addPage(page)
    

def call_read_api_resize(final_dest_url, temp_pdf_fp, pageIndex = None): 
    '''
    This is a much slower way to get OCR'd version of a PDF using Microsoft Read API. 
    It's intended for use on PDFs that failed processing by URL alone 
    due to their size -- e.g., above the max. dimensions that Read API supports. 
    
    Passed a URL that points to the PDF
    Downloads the PDF data to a temporary file (temp_pdf_fp), resizing pages if needed. 
    Loads and passes the data to a Read API call. 
    Deletes the temp file. 
    
    Note: optional argument to only get the first page, sometimes useful for testing. 
    
    Returns whether call was successful, as well as the JSON output of the OCR call. 
    '''
    
    pdf_data = requests.get(final_dest_url).content
    
    # A hacky way of figuring out whether the link points to a PDF or to an "error" page
    if not "%PDF" in str(pdf_data): 
        return "ERROR: URL does not point to PDF.", False
    
    # Use PyPDF2 to read the PDF data and write out a copy of that data, 
    # with pages resized if needed
    writer = PyPDF2.PdfFileWriter()
    reader = PyPDF2.PdfFileReader(io.BytesIO(pdf_data))
    
    if pageIndex: 
        add_page(reader, i, writer)
    else: 
        for i in range(reader.numPages): # loop through all pages
            add_page(reader, i, writer)
    
    # create temp file 
    with open(temp_pdf_fp, "wb") as f: 
        writer.write(f)
    
    output, success = call_read_api(flag = "pdf", image_path = temp_pdf_fp)
    
    # clean up
    os.remove(temp_pdf_fp)
    
    return output, success


# In[ ]:


def save_content(json_output, dest_fn):
    '''
    Given: JSON output & destination filepath (and filename)
    Saves content to the destination.
    '''
    print('Saving files to {}'.format(dest_fn))

    with open(dest_fn, 'w') as outfile:
        json.dump(json_output, outfile)


# In[ ]:


def bulk_ocr(fin_url_sublist, duplicates, failures, flag, 
             filepath_out = "/home/dssg-cfa/ke-gazettes/", temp_pdf_fp = "temp.pdf"):
    '''
    Loops through all final destination URLs in sublist. 
    Calls Read API to get and save json files for all of them. 
    Flag should be "url" or "pdf"
    '''
    calls = 0
    count = 0
    start_time = time.time()
    
    for final_dest_url in fin_url_sublist:
        print("starting on call " + str(calls))
        calls += 1
        # optional: add param: flag = connected_africa or flag = gazeti
        dest_fn = filepath_out + df.get_name(final_dest_url).strip().lower()
        if os.path.exists(dest_fn):
            print("Gazette already exists")
            # append to duplicates; don't call Read API
            duplicates.append({dest_fn: final_dest_url})
            continue

        # ----- CALL READ API AND SAVE OUTPUT ----- 
        # returns "analysis" variable from read API & whether call was successful 
        
        if flag == "url":
            json_output, success = call_read_api(final_dest_url)
        elif flag == "pdf":
            json_output, success = call_read_api_resize(final_dest_url, temp_pdf_fp)
        else: 
            print("Flag must be \'pdf\' or \'url\'")

        if success: 
            save_content(json_output, dest_fn)
            print("success " + str(count))
            count += 1

        # ----- ERROR HANDLING: IF OCR CALL DOESN'T GO THROUGH ----- 
        # append: error message (json_output), date of gazette, permanent image URL 
        else: 
            failures.append(final_dest_url)
            print('failed' + str(json_output) + ": " + str(failures[-1]))

    time_diff = time.time() - start_time
    print(str(time_diff/60) + " minutes for " + str(count) + " gazettes")
    print("Failed on " + str(len(failures)) + " gazettes.")
    # print("Duplicates: " + str(len(duplicates)))


# In[ ]:


def bulk_ocr_first_pg(filepath_url_metadata, src_database, failures,
                         temp_pdf_fp = "temp.pdf",
                         filepath_out = "/home/dssg-cfa/ke-gazettes-first-pgs/"):
    '''
    Loops through all final destination URLs in sublist. 
    Calls Read API to get and save json files for the first page of all files, 
    without filtering for duplicates. (Adds '*' if filename already exists.)
    Names files using metadata: 
    - Connected Africa: fileNameFromDB + "_" + src_database + "_" + checksums
    - Gazeti: fileNameDB + "_" + src_database + "_" + file_num
    '''
    if src_database not in ("connected-africa", "gazeti"): 
        print("src_database must be \'connected-africa\' or \'gazeti\'")
        return 
    
    calls = 0
    count = 0
    start_time = time.time()
    
    with open(filepath_url_metadata) as f:
        gazettes_src = json.load(f)
    
    for g in gazettes_src: 
        print("starting on call " + str(calls))
        calls += 1
        
        fileNameDB = g['fileNameDirectFromDB']
        final_dest_url = g['dest_url']
        if src_database == "connected-africa":
            checksums = g['checksums'][0]
            dest_fn = filepath_out + fileNameDB + "_" + src_database + "_" + checksums
        elif src_database == "gazeti":
            file_num = g['file_num']
            dest_fn = filepath_out + fileNameDB + "_" + src_database + "_" + file_num  
        while os.path.exists(dest_fn):
            dest_fn += "*"
        
        json_output, success = call_read_api_resize(final_dest_url, temp_pdf_fp, pageIndex = 0)
        
        if success: 
            save_content(json_output, dest_fn)
            print("success " + str(count))
            count += 1

        else: 
            failures.append(final_dest_url)
            print('failed' + str(json_output) + ": " + str(failures[-1]))

    time_diff = time.time() - start_time
    print(str(time_diff/60) + " minutes for " + str(count) + " gazettes")
    print("Failed on " + str(len(failures)) + " gazettes.")
    # print("Duplicates: " + str(len(duplicates)))


# In[ ]:


def call_form_rec_layout_api(url, pageIdx = None, pageIdxList = None, temp_pdf_fp = "temp.pdf"): 
    '''
    Cals form recognizer layout API on a given PDF document, identified by its URL and
    optional page indices. 
    pageIdx should be an integer (single page); pageIdxList should be a list of all pages
    to get form recognizer results for. 
    Returns success of operation and resulting JSON output. 
    '''
    
    # --- SETUP ---
    
    pdf_data = requests.get(url).content
    if not "%PDF" in str(pdf_data): 
        return "ERROR: URL does not point to PDF.", False

    writer = PyPDF2.PdfFileWriter()
    reader = PyPDF2.PdfFileReader(io.BytesIO(pdf_data))
    if pageIdx: 
        add_page(reader, pageIdx, writer)
    elif pageIdxList: 
        for i in pageIdxList: 
            add_page(reader, i, writer)
    else: 
        for i in range(reader.numPages): # loop through all pages
            add_page(reader, i, writer)
    
    with open(temp_pdf_fp, "wb") as f: 
        writer.write(f)
    
    # --- CALL FORM RECOGNIZER API ---
    
    # Endpoint URL
    endpoint = "<YOUR ENDPOINT HERE>"
    # subscription key 
    apim_key = "<YOUR APIM KEY HERE>"
    # constant
    post_url = endpoint + "/formrecognizer/v2.0/Layout/analyze"
    # replace with your PDF; note that this is a local file
    
    # SEND DATA TO SERVER
    
    source = temp_pdf_fp
    
    headers = {
        'Content-Type': 'application/pdf',
        'Ocp-Apim-Subscription-Key': apim_key,
    }
    with open(source, "rb") as f:
        data_bytes = f.read()

    try:
        resp = post(url = post_url, data = data_bytes, headers = headers)
        if resp.status_code != 202:
            print("POST analyze failed:\n%s" % resp.text)
            quit()
        print("POST analyze succeeded:\n%s" % resp.headers)
        get_url = resp.headers["operation-location"]
    except Exception as e:
        print("POST analyze failed:\n%s" % str(e))
        quit()
    
    # GET RESULTS FROM SERVER
    
    n_tries = 10
    n_try = 0
    wait_sec = 5
    while n_try < n_tries:
        try:
            resp = get(url = get_url, headers = {"Ocp-Apim-Subscription-Key": apim_key})
            resp_json = json.loads(resp.text)
            if resp.status_code != 200:
                print("GET Layout results failed:\n%s" % resp_json)
                return False, resp_json
            status = resp_json["status"]
            if status == "succeeded":
                print("Layout Analysis succeeded:\n%s" % resp_json)

            if status == "failed":
                print("Layout Analysis failed:\n%s" % resp_json)
                return False, resp_json
            # Analysis still running. Wait and retry.
            time.sleep(wait_sec)
            n_try += 1     
        except Exception as e:
            msg = "GET analyze results failed:\n%s" % str(e)
            print(msg)
            quit()
            
    return True, resp_json

