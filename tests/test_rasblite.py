#!/usr/bin/env python3

import unittest
import trace
import sys
import os
import urllib.request
import json
from ast import literal_eval
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from rasblite import engine

BASE_URL='/rest/api/1.0/'
SERVER_PORT = 8080

DEFAULT_MODEL = \
    """[Base]
        url = /rest/api/1.0/
        
        [Model]
        structure = 
            GET,POST         users/
            GET,PUT,DELETE   users/:userID/
            GET,PUT          users/:userID/name
            GET,POST         users/:userID/addresses/
            GET,PUT,DELETE   users/:userID/addresses/:address/
            GET,PUT          users/:userID/addresses/:address/address_lines
            GET,PUT          users/:userID/addresses/:address/post_code
            GET,PUT          users/:userID/age 
    """
DEFAULT_MODEL_STR = \
    """BASE URL = /rest/api/1.0/
STRUCTURE = {'users': {':userID': {'METHODS': 'GET,PUT,DELETE',
                       'addresses': {':address': {'METHODS': 'GET,PUT,DELETE',
                                                  'address_lines': {'METHODS': 'GET,PUT'},
                                                  'post_code': {'METHODS': 'GET,PUT'}},
                                     'METHODS': 'GET,POST'},
                       'age': {'METHODS': 'GET,PUT'},
                       'name': {'METHODS': 'GET,PUT'}},
           'METHODS': 'GET,POST'}}"""
DEFAULT_STARTING_DATA = "{'users': [{'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}], 'age': '21', 'name': 'Bob'}, {'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}], 'age': '60', 'name': 'Frank'}]}"

class TestModelParser(unittest.TestCase):
    def setUp(self):
        self.model_parser = engine.ModelParser()
        self.assertIsNotNone(self.model_parser, 'ModelParser did not initialise')

    def tearDown(self):
        pass


    def test_parse_default_starting_data(self):
        model = self.model_parser.parse(DEFAULT_MODEL, DEFAULT_STARTING_DATA)
        self.assertMultiLineEqual(str(model), DEFAULT_MODEL_STR, 'Model parsed from config seems different to model loaded')
        
        result = model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        ### User Bob
        result = model.action_path('GET', BASE_URL + 'users/0/')
        expected = literal_eval("{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}")
        self.assertDictEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/0/name')
        expected = 'Bob'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/0/age')
        expected = '21'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/0/addresses')
        expected = literal_eval("[{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        ### User Bob - Address 0
        
        result = model.action_path('GET', BASE_URL + 'users/0/addresses/0')
        expected = literal_eval("{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}")
        self.assertDictEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/0/addresses/0/address_lines')
        expected = '123 Fake Street'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/0/addresses/0/post_code')
        expected = 'AB12 3CD'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        ### User Frank
        result = model.action_path('GET', BASE_URL + 'users/1/')
        expected = literal_eval("{'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}")
        self.assertDictEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/name')
        expected = 'Frank'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/age')
        expected = '60'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses')
        expected = literal_eval("[{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        ### User Frank - Address 0
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses/0')
        expected = literal_eval("{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}")
        self.assertDictEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses/0/address_lines')
        expected = '456 My Street'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses/0/post_code')
        expected = 'EF45 6GH'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        ### User Frank - Address 1
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses/1')
        expected = literal_eval("{'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}")
        self.assertDictEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses/1/address_lines')
        expected = '789 Other Street'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
        result = model.action_path('GET', BASE_URL + 'users/1/addresses/1/post_code')
        expected = 'IJ12 3KL'
        self.assertEqual(result, expected, 'Starting data is different to expected')
        
class TestModelData(unittest.TestCase):
    def setUp(self):
        self.model_parser = engine.ModelParser()
        self.model = self.model_parser.parse(DEFAULT_MODEL, DEFAULT_STARTING_DATA)
        self.assertMultiLineEqual(str(self.model), DEFAULT_MODEL_STR, 'Model parsed from config seems different to model loaded')
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        
    def tearDown(self):
        pass

    def test_action_path_GET(self):
        
        # Check GET fails correctly
        result = self.model.action_path('GET', BASE_URL + 'users/999')
        expected = engine.ModelData.ModelError(error_type='BaseError')
        self.assertIsInstance(result, expected.__class__, 'model_object.action_path(GET,...) should have returned an error because this user id does not exist.')
        self.assertEqual(result.error_type, expected.error_type, 'model_object.action_path(GET,...) returned an error as expected but the error type was different.')
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/this_does_not_exist')
        expected = engine.ModelData.ModelError(error_type='BadRequestError')
        self.assertIsInstance(result, expected.__class__, 'model_object.action_path(GET,...) should have returned an error because the path does not exist.')
        self.assertEqual(result.error_type, expected.error_type, 'model_object.action_path(GET,...) returned an error as expected but the error type was different.')
        
        result = self.model.action_path('GET', BASE_URL + 'users/ten')
        expected = engine.ModelData.ModelError(error_type='BadRequestError')
        self.assertIsInstance(result, expected.__class__, 'model_object.action_path(GET,...) should have returned an error because a string was given instead of a number.')
        self.assertEqual(result.error_type, expected.error_type, 'model_object.action_path(GET,...) returned an error as expected but the error type was different.')
        
        # Exercise normal test routine
        
        ### User Bob
        result = self.model.action_path('GET', BASE_URL + 'users/0/')
        expected = literal_eval("{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/name')
        expected = 'Bob'
        self.assertEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/age')
        expected = '21'
        self.assertEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/addresses')
        expected = literal_eval("[{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
        ### User Bob - Address 0
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/addresses/0')
        expected = literal_eval("{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/addresses/0/address_lines')
        expected = '123 Fake Street'
        self.assertEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/0/addresses/0/post_code')
        expected = 'AB12 3CD'
        self.assertEqual(result, expected, 'model_object.action_path(GET,...) returned unexpected result')
        
    def test_action_path_POST(self):
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        # Check POST fails correctly
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.model.action_path('POST', BASE_URL + 'users/1/', message_body)
        expected = engine.ModelData.ModelError(error_type='BadRequestError')
        self.assertIsInstance(result, expected.__class__, 'model_object.action_path(POST,...) should have returned an error because the test data disallows POST here but ModelError was not returned.')
        self.assertEqual(result.error_type, expected.error_type, 'model_object.action_path(POST,...) returned an error as expected but the error type was different.')
        
        # Exercise normal test routine
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.model.action_path('POST', BASE_URL + 'users/', message_body)
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'model_object.action_path(POST,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently added user')
        
        message_body = literal_eval("{'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}")
        result = self.model.action_path('POST', BASE_URL + 'users/0/addresses/', message_body)
        expected = literal_eval("[{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(POST,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently added address')
    
    def test_action_path_PUT(self):
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        # Check PUT fails correctly
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.model.action_path('PUT', BASE_URL + 'users/', message_body)
        expected = engine.ModelData.ModelError(error_type='BadRequestError')
        self.assertIsInstance(result, expected.__class__, 'model_object.action_path(PUT,...) should have returned an error because the test data disallows PUT here but ModelError was not returned.')
        self.assertEqual(result.error_type, expected.error_type, 'model_object.action_path(PUT,...) returned an error as expected but the error type was different.')
        
        # Exercise normal test routine
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}")
        result = self.model.action_path('PUT', BASE_URL + 'users/1/', message_body)
        expected = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(PUT,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently updated details')
        
        message_body = 'Sarah'
        result = self.model.action_path('PUT', BASE_URL + 'users/0/name', message_body)
        expected = literal_eval("{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(PUT,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently updated details')
        
        message_body = '44'
        result = self.model.action_path('PUT', BASE_URL + 'users/1/age', message_body)
        expected = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '44'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(PUT,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently updated details')
        
        message_body = literal_eval("{'post_code': 'AB55 9TT', 'address_lines': '46 Test Road'}")
        result = self.model.action_path('PUT', BASE_URL + 'users/1/addresses/0/', message_body)
        expected = literal_eval("{'post_code': 'AB55 9TT', 'address_lines': '46 Test Road'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(PUT,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'address_lines': '46 Test Road', 'post_code': 'AB55 9TT'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently updated details')
        
        message_body = '77 Roundabout Street'
        result = self.model.action_path('PUT', BASE_URL + 'users/1/addresses/1/address_lines/', message_body)
        expected = literal_eval("{'post_code': 'CC44 3YY', 'address_lines': '77 Roundabout Street'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(PUT,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'address_lines': '46 Test Road', 'post_code': 'AB55 9TT'}, {'post_code': 'CC44 3YY', 'address_lines': '77 Roundabout Street'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently updated details')
        
        message_body = 'ZY99 8XR'
        result = self.model.action_path('PUT', BASE_URL + 'users/1/addresses/0/post_code/', message_body)
        expected = literal_eval("{'address_lines': '46 Test Road', 'post_code': 'ZY99 8XR'}")
        self.assertDictEqual(result, expected, 'model_object.action_path(PUT,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'address_lines': '46 Test Road', 'post_code': 'ZY99 8XR'}, {'post_code': 'CC44 3YY', 'address_lines': '77 Roundabout Street'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently updated details')
        
        
    def test_action_path_DELETE(self):
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'Starting data is different to expected')
        
        # Check DELETE fails correctly
        result = self.model.action_path('DELETE', BASE_URL + 'users/0/name')
        expected = engine.ModelData.ModelError(error_type='BadRequestError')
        self.assertIsInstance(result, expected.__class__, 'model_object.action_path(DELETE,...) should have returned an error because the test data disallows DELETE here but ModelError was not returned.')
        self.assertEqual(result.error_type, expected.error_type, 'model_object.action_path(DELETE,...) returned an error as expected but the error type was different.')
        
        # Exercise normal test routine
        result = self.model.action_path('DELETE', BASE_URL + 'users/0/')
        expected = literal_eval("[{'name': '', 'addresses': [], 'age': ''}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(DELETE,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': '', 'addresses': [], 'age': ''}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently deleted user')
        
        result = self.model.action_path('DELETE', BASE_URL + 'users/1/addresses/1')
        expected = literal_eval("[{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': '', 'address_lines': ''}]")
        self.assertListEqual(result, expected, 'model_object.action_path(DELETE,...) returned unexpected result')
        
        result = self.model.action_path('GET', BASE_URL + 'users/')
        expected = literal_eval("[{'name': '', 'addresses': [], 'age': ''}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': '', 'address_lines': ''}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'model_object.action_path(GET,...) didn\'t show the recently deleted address')
        
        
class TestRequestHandler(unittest.TestCase):
    
    def setUp(self):
        self.controller = engine.Controller(DEFAULT_MODEL, DEFAULT_STARTING_DATA, SERVER_PORT)
        self.controller.start()
        
    def tearDown(self):
        self.controller.stop()
        
    def server_request(self, method, url_path, data=None):
        full_url = 'http://localhost:' + str(SERVER_PORT) + BASE_URL + url_path
        if data:
            data = json.dumps(data).encode('utf8')
        
        request = urllib.request.Request(method=method, 
                                         url=full_url,
                                         data=data, 
                                         headers={'Content-Type': 'application/json'})
        
        try:
            raw_response = urllib.request.urlopen(request).read()
            return self.controller.parse_response(raw_response)
        except urllib.error.URLError as error:
            # This will catch urllib.error.HTTPError too
            return error
    
    def test_set_controller(self):
        # Have to use getattr to surpress warnings about  RequestHandler.controller
        self.assertEqual(getattr(engine.RequestHandler, 'controller'), self.controller, "RequestHandler should have a reference to this controller. Did the member variable name change?")
        
    def test_request_GET(self):
        # Verify starting data
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertNotIsInstance(result, urllib.error.URLError, 'server_request failed with error: ' + str(result))
        self.assertListEqual(result, expected, 'Starting data appears to be different to what was expected. This will cause the subsequent tests to fail')
        
        
        # Check GET fails correctly
        result = self.server_request('GET', 'users/999')
        self.assertIsInstance(result, urllib.error.URLError, 'self.server_request(GET,...) should have returned an error because this user id does not exist.')
        self.assertEqual(result.code, 404, 'self.server_request(GET,...) returned an error as expected but the error code was different.')
         
        result = self.server_request('GET', 'users/0/this_does_not_exist')
        self.assertIsInstance(result, urllib.error.URLError, 'self.server_request(GET,...) should have returned an error because the path does not exist.')
        self.assertEqual(result.code, 400, 'self.server_request(GET,...) returned an error as expected but the error code was different.')
         
        result = self.server_request('GET', 'users/ten')
        self.assertIsInstance(result, urllib.error.URLError, 'self.server_request(GET,...) should have returned an error because a string was given instead of a number.')
        self.assertEqual(result.code, 400, 'self.server_request(GET,...) returned an error as expected but the error code was different.')
         
        # Exercise normal test routine
         
        ### User Bob
        result = self.server_request('GET', 'users/0/')
        expected = literal_eval("{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}")
        self.assertDictEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/0/name')
        expected = 'Bob'
        self.assertEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/0/age')
        expected = '21'
        self.assertEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/0/addresses')
        expected = literal_eval("[{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
         
        ### User Bob - Address 0
         
        result = self.server_request('GET', 'users/0/addresses/0')
        expected = literal_eval("{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}")
        self.assertDictEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/0/addresses/0/address_lines')
        expected = '123 Fake Street'
        self.assertEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/0/addresses/0/post_code')
        expected = 'AB12 3CD'
        self.assertEqual(result, expected, 'self.server_request(GET,...) returned unexpected result')
        
        
    def test_request_POST(self):
        # Verify starting data
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertNotIsInstance(result, urllib.error.URLError, 'server_request failed with error: ' + str(result))
        self.assertListEqual(result, expected, 'Starting data appears to be different to what was expected. This will cause the subsequent tests to fail')
         
        # Check POST fails correctly
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.server_request('POST', 'users/1/', message_body)
        self.assertIsInstance(result, urllib.error.URLError, 'self.server_request(POST,...) should have returned an error because the test data disallows POST here.')
        self.assertEqual(result.code, 400, 'self.server_request(POST,...) returned an error as expected but the error code was different.')
         
        # Exercise normal test routine
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.server_request('POST', 'users/', message_body)
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'self.server_request(POST,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently added user')
           
        message_body = literal_eval("{'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}")
        result = self.server_request('POST', 'users/0/addresses/', message_body)
        expected = literal_eval("[{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}]")
        self.assertListEqual(result, expected, 'self.server_request(POST,...) returned unexpected result')
           
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently added address')
        
    def test_request_PUT(self):
        # Verify starting data
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertNotIsInstance(result, urllib.error.URLError, 'server_request failed with error: ' + str(result))
        self.assertListEqual(result, expected, 'Starting data appears to be different to what was expected. This will cause the subsequent tests to fail')
        
        # Check PUT fails correctly
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.server_request('PUT', 'users/', message_body)
        self.assertIsInstance(result, urllib.error.URLError, 'self.server_request(PUT,...) should have returned an error because the test data disallows PUT here.')
        self.assertEqual(result.code, 400, 'self.server_request(PUT,...) returned an error as expected but the error code was different.')
        
        # Exercise normal test routine
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}")
        result = self.server_request('PUT', 'users/1/', message_body)
        expected = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
          
        message_body = 'Sarah'
        result = self.server_request('PUT', 'users/0/name', message_body)
        expected = literal_eval("{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '18'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
          
        message_body = '44'
        result = self.server_request('PUT', 'users/1/age', message_body)
        expected = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '44'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
          
        message_body = literal_eval("{'post_code': 'AB55 9TT', 'address_lines': '46 Test Road'}")
        result = self.server_request('PUT', 'users/1/addresses/0/', message_body)
        expected = literal_eval("{'post_code': 'AB55 9TT', 'address_lines': '46 Test Road'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'address_lines': '46 Test Road', 'post_code': 'AB55 9TT'}, {'post_code': 'CC44 3YY', 'address_lines': '11 Testing Avenue'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
          
        message_body = '77 Roundabout Street'
        result = self.server_request('PUT', 'users/1/addresses/1/address_lines/', message_body)
        expected = literal_eval("{'post_code': 'CC44 3YY', 'address_lines': '77 Roundabout Street'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'address_lines': '46 Test Road', 'post_code': 'AB55 9TT'}, {'post_code': 'CC44 3YY', 'address_lines': '77 Roundabout Street'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
          
        message_body = 'ZY99 8XR'
        result = self.server_request('PUT', 'users/1/addresses/0/post_code/', message_body)
        expected = literal_eval("{'address_lines': '46 Test Road', 'post_code': 'ZY99 8XR'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Jim', 'addresses': [{'address_lines': '46 Test Road', 'post_code': 'ZY99 8XR'}, {'post_code': 'CC44 3YY', 'address_lines': '77 Roundabout Street'}], 'age': '44'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
        
    def test_request_DELETE(self):
        # Verify starting data
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertNotIsInstance(result, urllib.error.URLError, 'server_request failed with error: ' + str(result))
        self.assertListEqual(result, expected, 'Starting data appears to be different to what was expected. This will cause the subsequent tests to fail')
        
        # Check DELETE fails correctly
        result = self.server_request('DELETE', 'users/0/name')
        expected = engine.ModelData.ModelError(error_type='BadRequestError')
        self.assertIsInstance(result, urllib.error.URLError, 'self.server_request(DELETE,...) should have returned an error because the test data disallows DELETE here.')
        self.assertEqual(result.code, 400, 'self.server_request(DELETE,...) returned an error as expected but the error code was different.')

        # Exercise normal test routine
        result = self.server_request('DELETE', 'users/0/')
        expected = literal_eval("[{'name': '', 'addresses': [], 'age': ''}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'self.server_request(DELETE,...) returned unexpected result')
        
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': '', 'addresses': [], 'age': ''}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently deleted user')
        
        result = self.server_request('DELETE', 'users/1/addresses/1')
        expected = literal_eval("[{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': '', 'address_lines': ''}]")
        self.assertListEqual(result, expected, 'self.server_request(DELETE,...) returned unexpected result')
        
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': '', 'addresses': [], 'age': ''}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': '', 'address_lines': ''}], 'age': '60'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently deleted address')
        
    def test_request_ALL(self):
        # Verify starting data
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Bob', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'name': 'Frank', 'addresses': [{'post_code': 'EF45 6GH', 'address_lines': '456 My Street'}, {'post_code': 'IJ12 3KL', 'address_lines': '789 Other Street'}], 'age': '60'}]")
        self.assertNotIsInstance(result, urllib.error.URLError, 'server_request failed with error: ' + str(result))
        self.assertListEqual(result, expected, 'Starting data appears to be different to what was expected. This will cause the subsequent tests to fail')
        
        # Exercise normal test routine
        message_body = literal_eval("{'name': 'Jim', 'addresses': [{'post_code': 'UR98 7ST', 'address_lines': '30 Flat Road'}], 'age': '18'}")
        result = self.server_request('POST', 'users/', message_body)
        expected = literal_eval("[{'age': '21', 'name': 'Bob', 'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}]}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'self.server_request(POST,...) returned unexpected result')
        
        message_body = 'Sarah'
        result = self.server_request('PUT', 'users/0/name', message_body)
        expected = literal_eval("{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
          
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'age': '18', 'name': 'Jim', 'addresses': [{'address_lines': '30 Flat Road', 'post_code': 'UR98 7ST'}]}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
        
        message_body = literal_eval("{'name': 'Dan', 'addresses': [{'post_code': 'GT58 8WW', 'address_lines': '3 Shape Road'}], 'age': '26'}")
        result = self.server_request('PUT', 'users/2/', message_body)
        expected = literal_eval("{'name': 'Dan', 'addresses': [{'post_code': 'GT58 8WW', 'address_lines': '3 Shape Road'}], 'age': '26'}")
        self.assertDictEqual(result, expected, 'self.server_request(PUT,...) returned unexpected result')
         
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}], 'age': '21'}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'name': 'Dan', 'addresses': [{'post_code': 'GT58 8WW', 'address_lines': '3 Shape Road'}], 'age': '26'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently updated details')
        
        message_body = literal_eval("{'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}")
        result = self.server_request('POST', 'users/0/addresses/', message_body)
        expected = literal_eval("[{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}]")
        self.assertListEqual(result, expected, 'self.server_request(POST,...) returned unexpected result')
           
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}], 'age': '21'}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'name': 'Dan', 'addresses': [{'post_code': 'GT58 8WW', 'address_lines': '3 Shape Road'}], 'age': '26'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently added address')
        
        result = self.server_request('DELETE', 'users/1/addresses/0')
        expected = literal_eval("[{'address_lines': '', 'post_code': ''}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]")
        self.assertListEqual(result, expected, 'self.server_request(DELETE,...) returned unexpected result')
        
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}], 'age': '21'}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '', 'post_code': ''}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'name': 'Dan', 'addresses': [{'post_code': 'GT58 8WW', 'address_lines': '3 Shape Road'}], 'age': '26'}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently deleted address')
        
        result = self.server_request('DELETE', 'users/2/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}], 'age': '21'}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '', 'post_code': ''}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'name': '', 'addresses': [], 'age': ''}]")
        self.assertListEqual(result, expected, 'self.server_request(DELETE,...) returned unexpected result')
        
        result = self.server_request('GET', 'users/')
        expected = literal_eval("[{'name': 'Sarah', 'addresses': [{'post_code': 'AB12 3CD', 'address_lines': '123 Fake Street'}, {'post_code': 'EE55 1FF', 'address_lines': '99 Oak Avenue'}], 'age': '21'}, {'age': '60', 'name': 'Frank', 'addresses': [{'address_lines': '', 'post_code': ''}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}]}, {'name': '', 'addresses': [], 'age': ''}]")
        self.assertListEqual(result, expected, 'self.server_request(GET,...) didn\'t show the recently deleted user')
        

if __name__ == '__main__': 
    traceObj = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix], count=1, trace=0)
    traceObj.runfunc(unittest.main, exit=False)
    results = traceObj.results()
    results.write_results(summary=True, coverdir='.')
    
    
