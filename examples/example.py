#!/usr/bin/env python3
"""
This script demonstrates how to call the rasblite module from another Python 
script.
"""

import json
import urllib.request
import sys
import os

# If the user hasn't installed rasblite then try to find it in this repo.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from rasblite import engine

PORT = 8080
MODEL = """
[Base]
url = /api/

[Model]
structure = 
    GET,POST         items/
    GET,PUT,DELETE   items/:item_number/
    GET,PUT          items/:item_number/name
    GET,PUT          items/:item_number/amount
"""

def verify_my_client(response_parsing_function):
    """As an example, this adds {'name': 'Milk', 'amount': 1} to ../api/items and
    then immediately retrieves the name of the item inserted (which is of course
    Milk).
    
    :param function response_parsing_function: function to use to parse the response
    """
    url = 'http://localhost:' + str(PORT) + '/api/items/'
    data = json.dumps({'name': 'Milk', 'amount': 1}).encode('utf8')
    post_request = urllib.request.Request(method='POST', 
                                         url=url,
                                         data=data, 
                                         headers={'Content-Type': 'application/json'})

    raw_post_response = urllib.request.urlopen(post_request).read()
    
    print(response_parsing_function(raw_post_response))
    
    get_request = urllib.request.Request(method='GET', url=url + '0/name/')
    raw_get_response = urllib.request.urlopen(get_request).read()
    
    print(response_parsing_function(raw_get_response))
    
if __name__ == '__main__':
    """This is a brief example on how to use the rasblite module."""
    print('start')
    rasbliteController = engine.Controller(MODEL, 'DEFAULT', PORT)
    rasbliteController.start()
    
    verify_my_client(rasbliteController.parse_response)
    
    rasbliteController.stop()
    print('end')
