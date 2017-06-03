"""
The rasblite engine module contains the core logic for the Lightweight RESTful API 
Server Builder. This module is not intended to be ran directly by the user - rather
it is designed to be used by client views (such as other scripts, apps, etc.) 
The module broadly follows the MVC pattern where the :class:`rasblite.engine.Controller`
is the controller, :class:`rasblite.engine.RequestHandler` is the view and 
:class:`rasblite.engine.ModelData` makes up the model. 
"""

import http.server
import configparser
import re
import json
import os
from pprint import pprint, pformat
from ast import literal_eval
from threading import Thread

RESOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))

# TODO: Should use Python's logging module rather than just prints

class ModelParser(object):
    """The rasblite ModelParser's main funtion is to create and populate a 
    class:`rasblite.engine.ModelData` object by translating from a raw model and
    data. The ModelParser's job is to understand the format of the raw model 
    structure which acts as a blueprint so that it can parse it into a new 
    :class:`rasblite.engine.ModelData` object. This is then populated using the 
    starting data provided.
    """

    KEY_BASE = 'Base'
    KEY_MODEL = 'Model'
    KEY_URL = 'URL'
    KEY_STRUCTURE = 'STRUCTURE'
    KEY_METHODS = 'METHODS'
    RE_STRUCTURE = r'[\s]+(?P<Methods>(?:(?:GET|POST|PUT|DELETE),?)+)[\t ]+(?P<Pattern>[\w/:]+)'
    
    def __starting_data_mode_empty(self, model_structure):
        """Returns a completely empty data store which does not even contain the
        structure of the raw model. To get an empty data store that conforms to
        the model then use __starting_data_mode_default.
        """
        return dict()
    
    def __walk_model_structure(self, data_store, current_key, model_structure):
        """Walks (recursively) the raw model structure creating an empty data store
        that contains the same structure as the model.
        """
        item = model_structure[current_key]
        if isinstance(item, dict):
            for new_key in item:
                if new_key == self.KEY_METHODS:
                    continue
                
                if new_key[0] == ':':
                    data_store[current_key] = list()
                else:
                    data_store[current_key][new_key] = dict()
                    self.__walk_model_structure(data_store[current_key], new_key, item)

    def __starting_data_mode_default(self, model_structure):
        """Returns a data store with a structure that matches the model but it 
        is initially empty.
        """
        # TODO: Could this method be merged with the walk method? Need to use key rather than passing the model_structure
        data_store = dict()
        
        for current_key in model_structure:
            if current_key == self.KEY_METHODS:
                continue
            if current_key[0] == ':':
                data_store = list()
                break
            else:
                data_store[current_key] = dict()
                self.__walk_model_structure(data_store, current_key, model_structure)

        return data_store


    def __starting_data_mode_example(self, model_structure):
        """Returns a data store with example data that conforms to the raw model
        structure held within model.txt.
        """
        return {'users': [{'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}], 'age': '21', 'name': 'Bob'}, {'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}], 'age': '60', 'name': 'Frank'}]}
    
    def __verify_data_for_data_store(self, data_key, new_data, model_structure):
        """Walks (recursively) the model and data structure and verifies that
        they both match the same structure. Returns True if the data contains 
        the same structure as the model
        """
        item = new_data[data_key]
        try:
            model_item = model_structure[data_key]
        except KeyError as key_error:
            print("Error: Data contains extra identifier not in the model: {0}".format(key_error))
            return False
            
        if isinstance(item, list):
            # Check that the model says this item should have a list
            model_item_contains_list = False
            for model_key in model_item:
                if model_key == self.KEY_METHODS:
                    continue
                elif model_key[0] == ':':
                    model_item = model_item[model_key]
                    model_item_contains_list = True
                    break
                
            if model_item_contains_list:
                for next_item in item:
                    if isinstance(next_item, dict):
                        for next_key in next_item:
                            successful = self.__verify_data_for_data_store(next_key, next_item, model_item)
                            if not successful:
                                return False
                    elif isinstance(next_item, list):
                        print('ERROR: Cannot have a list contain another list')
                        return False
                    else:
                        print('ERROR: List containing item that is not a list or dict')
                        return False
                        
                return True
            else:
                print('ERROR: data contains a list but the model doesn\'t')
                return False
        elif isinstance(item, str):
            if len(model_item) == 1 and self.KEY_METHODS in model_item:
                return True
            else:
                print('ERROR: Data contains a string but model is expecting a dictionary or list')
                return False
        elif isinstance(item, dict):
            print('Handle dictionary')
            model_item_contains_dict = False
            for model_key in model_item:
                if model_key == self.KEY_METHODS:
                    continue
                elif model_key[0] != ':':
                    model_item_contains_dict = True
                    break
                
            if model_item_contains_dict:
                for next_key in item:
                    successful = self.__verify_data_for_data_store(next_key, item, model_item)
                    if not successful:
                        return False
                return True
            else:
                print('ERROR: data contains a dictionary but the model doesn\'t')
                return False
        else:
            print('ERROR: unhandled type' + item.__class__.__name__)
            return False
        
                    
        
    
    STARTING_DATA_MODES = {'EMPTY' :   __starting_data_mode_empty, 
                           'DEFAULT' : __starting_data_mode_default, 
                           'EXAMPLE' : __starting_data_mode_example}
    
    def parse(self, raw_model, raw_data):
        """Parses the raw model to create a :class:`rasblite.engine.ModelData`
        object which is then populated with starting data if supplied.
        
        :param str raw_model: contents of the model structure config
        :param str raw_data: either a special string which tells the 
            :class:`rasblite.engine.ModelParser` how to construct the starting
            data or the contents of the actual data
        :returns: a new :class:`rasblite.engine.ModelData` object containing the 
            structure provided and populated with the starting data provided
        :rtype: :class:`rasblite.engine.ModelData`
        """
        config = configparser.ConfigParser()
        config.read_string(raw_model)
        
        model = ModelData()
        
        base_url = config[self.KEY_BASE][self.KEY_URL]
        model._base_url = base_url
        
        raw_structure = config[self.KEY_MODEL][self.KEY_STRUCTURE]
        model._structure = self.__parse_structure(raw_structure)
        model._data_store = self.__parse_data(model._structure, raw_data)
        
        
        return model

    def __parse_structure(self, raw_structure):
        """Parses the raw model structure and returns a dictionary containing 
        this structure.
        """
        structure = dict()

        matches = re.findall(self.RE_STRUCTURE, raw_structure)
        
        for methods,pattern in matches:
            pattern_parts = pattern.split('/')
            
            curr_dict = structure
            for part in pattern_parts:
                if not part:
                    continue
                
                if part not in curr_dict:
                    curr_dict[part] = {self.KEY_METHODS:methods}
                    
                curr_dict = curr_dict[part]
        
        return structure
    
    def __parse_data(self, model_structure, raw_data):
        """Parses the raw data to create starting data for the model. The model
        structure is used to ensure the data matches the model. The raw data
        can also contain a special string that the ModelParser understands to
        construct the starting data itself. 
        """
        data_store = dict()
        
        if not raw_data:
            raw_data = 'EMPTY'
        
        if raw_data in self.STARTING_DATA_MODES:
            data_store = self.STARTING_DATA_MODES[raw_data](self, model_structure)
        else:
            # TODO: If we trust the data we could just set it like data_store = literal_eval(raw_data)
            data_matches_model = True
            new_data = literal_eval(raw_data)
            for data_key in new_data:
                data_matches_model = self.__verify_data_for_data_store(data_key, new_data, model_structure)
                if not data_matches_model:
                    break
            if data_matches_model:
                print('Successful! Data matches model')
                data_store = literal_eval(raw_data)
        
        return data_store
    

class ModelData():
    """The rasblite ModelData holds both the structure of the data and the 
    data store. It is smarter than just a store though as it provides a way to
    perform actions on the data such as adding, reading and deleting the data it
    holds by supplying it with REST intents. The ModelData is constructed by a
    :class:`rasblite.engine.ModelParser` which in turn takes in a raw model and
    starting data.
    """
    
    class ModelError():
        """The ModelError class represents errors when accessing 
        :class:`rasblite.engine.ModelData`. For example a ModelError is raised if
        the user tries to read data that does not conform to the held model.
        """
        def __init__(self, error_type='GenericError', message=''):
            """Creates a new ModelError with a type and message.
            
            :param str error_type: type of ModelError. GenericError is used if
                no type is given
            :param str message: description of the actual issue that occured
            """
            self.error_type = error_type
            self.message = message
            
    def __init__(self):
        """Creates a new ModelData with starting (empty) defaults.
        """
        self._structure = dict()
        self._base_url = ''
        
    def __repr__(self):
        """Returns a string representation of the ModelData.
        """
        desc_string = ''
        desc_string += 'BASE URL = ' + self._base_url
        desc_string += '\nSTRUCTURE = ' + pformat(self._structure)
        
        return desc_string
    
    def __verify_base_url(self, path):
        """Verifies the base url used matches the one that is held by the model,
        returning True if it does.
        """
        if len(path) < len(self._base_url):
            return False

        sub_path = path[:len(self._base_url)]

        return (sub_path.lower() == self._base_url)
    
    def action_path(self, method, path, message_body=None):
        """Carries out the user's instruction depending on the method (GET,POST,
        PUT or DELETE) and returns either the data requested or a 
        :class:`rasblite.engine.ModelData.ModelError` if there was an issue.
        
        :param str method: HTTP method used such as GET, POST, PUT or DELETE
        :param str path: full url requested by the user
        :param str message_body: data from the HTTP body (such as data to be put
            into the model)
        :returns: data requested by the user or a 
            :class:`rasblite.engine.ModelData.ModelError`
        :rtype: str, dict, list or :class:`rasblite.engine.ModelData.ModelError`
        """
        valid_base_path = self.__verify_base_url(path)
        if not valid_base_path:
            return self.ModelError(error_type='BaseError')
        
        path = path[len(self._base_url):]
        path_parts = path.split('/')
        
        if path:
            result = self.__walk_structure_tree(method, None, message_body, self._structure, path_parts, list(), list())
        else:
            result =  ModelData.ModelError(error_type='BaseError')
            
        return result

    
    def __walk_structure_tree(self, method, allowed_methods, message_body, structure, path_parts, previous_parts, previous_keys):
        """There are two main parts to this function. The first part walks 
        (recursively) through the model to drill down to the requested point to
        verify the request matches the model held. A ModelError is returned if 
        this is not the case (for example if the request has not been allowed 
        for this HTTP method). Once the correct location has been found within
        the model, the second part is the data is then transversed to perform 
        the actual requested action on the data store. 
        """
        print('structure', structure)
        print('path_parts', path_parts)
        
        if not path_parts:
            if method in allowed_methods.split(','):
                return self.__walk_data_store(method, message_body, self._data_store, None, None, previous_parts, previous_keys)
            else:
                result = ModelData.ModelError(error_type='BadRequestError')
                return result
        
        for current_node in path_parts:
            if current_node == '':
                if method in allowed_methods.split(','):
                    return self.__walk_data_store(method, message_body, self._data_store, None, None, previous_parts, previous_keys)
                else:
                    result = ModelData.ModelError(error_type='BadRequestError')
                    return result
            
            for key in structure:
                if key == ModelParser.KEY_METHODS:
                    continue
                
                if key == current_node or (key[0] == ':' and current_node.isdigit()):
                    detail = structure[key]
                    allowed_methods = detail[ModelParser.KEY_METHODS]
                    previous_keys.append(key)
                    result = self.__walk_structure_tree(method, allowed_methods, message_body, detail, path_parts[1:], previous_parts + path_parts[:1], previous_keys)
                    if result is not None:
                        return result
                    else:
                        result = ModelData.ModelError(error_type='BadRequestError')
                        return result
                    
    def __walk_data_store(self, method, message_body, read_only_detail, current_key, previous_detail, previous_parts, previous_keys):
        """Walks (recursively) through the data to perform the requested action 
        on the data store. This could be reading the data at a certain point if
        the HTTP method is GET or it could be placing new data if the HTTP
        method is PUT or POST for example.
        """
        # TODO: Probably need to return a status code too, such as 204
        if not previous_parts:
            if method == 'GET':
                return read_only_detail
            elif method == 'POST':
                # TODO: We check the model up to the point we insert but we don't verify underneath. Therfore it's possible to insert rubbish.
                read_only_detail.append(message_body)
                return read_only_detail
            elif method == 'PUT':
                # TODO: Should break PUT into a separate method
                if not isinstance(read_only_detail, type(message_body)):
                    print('ERROR data provided is not of the same type')
                    return ModelData.ModelError(error_type='BadRequestError')
                elif isinstance(read_only_detail, dict):
                    
                    for new_key, new_value in message_body.items():
                        previous_detail[current_key][new_key] = new_value
                else:
                    previous_detail[current_key] = message_body
                
                # If we've updated an item field then return the whole object
                # otherwise if the whole object has been updated then return it
                if isinstance(current_key, int):
                    return previous_detail[current_key]
                else:
                    return previous_detail
            elif method == 'DELETE':
                self.__perform_delete(previous_detail, current_key)
                
                return previous_detail
        
        for current_node in previous_parts:

            
            if previous_keys[0][0] == ':':
                if not current_node.isdigit():
                    print('ERROR should be a number index')
                    return ModelData.ModelError(error_type='BadRequestError')
                index = int(current_node)
                
                if index >= len(read_only_detail):
                    print('ERROR number higher than size of collection')
                    return ModelData.ModelError(error_type='BaseError')
                
                return self.__walk_data_store(method, message_body, read_only_detail[index], index, read_only_detail, previous_parts[1:], previous_keys[1:] )
            else:
                if current_node not in read_only_detail:
                    print('ERROR Model allowed \'' + current_node + '\' but the data store does not contain it.')
                    return ModelData.ModelError(error_type='BaseError')
                return self.__walk_data_store(method, message_body, read_only_detail[current_node], current_node, read_only_detail, previous_parts[1:], previous_keys[1:]) 
            
    def __perform_delete(self, previous_detail, current_key):
        """Carries out a delete on the data (for example if the HTTP method used
        was DELETE) which replaces the requested point with an empty object of
        that type. Deletes will also do the same to anything underneath them in
        the model structure.
        """
        if isinstance(previous_detail[current_key], dict):
            for new_key in previous_detail[current_key]:
                self.__perform_delete(previous_detail[current_key], new_key)
        else:
            previous_type = type(previous_detail[current_key])
            empty_object = previous_type()
            previous_detail[current_key] = empty_object


class RequestHandler(http.server.BaseHTTPRequestHandler):
    """The RequestHandler deals with requests from the HTTP interface and performs
    those requests on the :class:`rasblite.engine.Controller`. The RequestHandler
    also handles the responses back from the :class:`rasblite.engine.Controller`
    so that it can be displayed to the user.
    """
    
    @classmethod
    def set_controller(cls, controller):
        """Sets which :class:`rasblite.engine.Controller` to use by the RequestHandler
        
        :param rasblite.engine.Controller controller: controller to use
        """
        cls.controller = controller
    
    @classmethod
    def parse_response(self, raw_response):
        """Parses the response (HTTP body) into a Python collection, if applicable.
        For example, if the HTTP response body contained `<\html><h1>['a','b']</h1></html>`
        a Python :class:`list` would be returned with two elements, a and b.
        
        This function is useful because in the future the response from the 
        :class:`rasblite.engine.RequestHandler` may change to add extra info
        but this function will make sure external users are not impacted.
        
        :param bytes raw_response: raw bytes representing the HTTP body / payload
        :returns: decoded object from the raw response
        :rtype: str, list, dict (depending on raw_response)
        """
        
        if not raw_response:
            return None
        
        matchObj = re.match(r'<html><h1>(.+)</h1></html>', raw_response.decode('utf8'))
        if matchObj:
            
            parsed_response = matchObj.group(1)
            if ('[' in parsed_response and ']' in parsed_response) or \
               ('{' in parsed_response and '}' in parsed_response):
                parsed_response = literal_eval(matchObj.group(1))
            
            if parsed_response:
                return parsed_response
            else:
                print('ERROR: RequestHandler could not retrieve an object from the response.')
                return None
        else:
            print('ERROR: RequestHandler response format has changed. The regex needs to be updated.')
            return None
         
    def get_message_body(self):
        """Returns the HTTP body (response payload) parsed into an appropiate 
        Python type.
        
        :returns: Python object representation of the HTTP response
        :rtype: str, list, dict
        """
        content_len = int(self.headers.get('content-length', 0))
        raw_message_body = self.rfile.read(content_len)
        
        content_type = self.headers.get('content-type', '')
        if content_type == 'application/json':
            return json.loads(raw_message_body.decode())
        else:
            return raw_message_body
    
    
    def do_GET(self):
        """Serves a GET request."""

        if 'favicon.ico' in self.path:
            favicon_path = os.path.join(RESOURCE_DIR, 'favicon.ico')
            self.__send_response(ctype='image/x-icon', 
                                 content=open(favicon_path, 'rb').read())
        else:
            controller = RequestHandler.controller
            result = controller.perform_user_request('GET', self.path)
            self.__handle_result(result)
            
    def do_POST(self):
        """Serves a POST request.
        """
        message_body = self.get_message_body()
        
        controller = RequestHandler.controller
        result = controller.perform_user_request('POST', self.path, message_body)
        self.__handle_result(result)
        
    def do_PUT(self):
        """Serves a PUT request.
        """
        message_body = self.get_message_body()
        
        controller = RequestHandler.controller
        result = controller.perform_user_request('PUT', self.path, message_body)
        self.__handle_result(result)
        
    def do_DELETE(self):
        """Serves a DELETE request.
        """
        controller = RequestHandler.controller
        result = controller.perform_user_request('DELETE', self.path)
        self.__handle_result(result)
        
            
    def __handle_result(self, result):
        """Handles the result from the Controller. For example this could be
        displaying the requested data or showing an error message.
        """
        if result is None:
            result = ModelData.ModelError(error_type='BaseError')
            
        if isinstance(result, ModelData.ModelError):
            self.handle_model_error(result)
        else:
            self.handle_model_success(result)
            
        
    def __send_response(self, content=None, ctype='text/html', 
                        status=200):
        """Sends a HTTP response back to the user with a format defined by the
        caller.
        """
        if 'text/html' in ctype:
                content = '<html>' + content + '</html>'
                content = content.encode()

        
        self.send_response(200)
        if content:
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", len(content))
            
        self.end_headers()
        
        self.wfile.write(content)


    def handle_model_error(self, model_error):
        """Handles the response back to the user after a model error.
        
        :param rasblite.engine.ModelData.ModelError model_error: error
            that was raised by the user's request.
        """
        if model_error.error_type == 'BaseError':
            self.send_error(404, "Page not found")
            return
        elif model_error.error_type == 'BadRequestError':
            self.send_error(400, "Invalid HTTP method or arguments")
            return
            
        
        self.send_error(404, "Page not found")
             
    
    def handle_model_success(self, data):
        """Handles the response back to the user after a successful request.
        
        :param str,dict,list data: either the data requested or other data 
            relating to the user's request.
        """
        self.__send_response('<h1>' + str(data) + '</h1>')
        
    

class Controller(object):
    """The rasblite Controller is the public-facing entry point to external scripts.
    It is responsible for standing up the HTTP server as well as passing on 
    information to and from the other parts of the module. The Controller
    primarily interacts with the :class:`rasblite.engine.RequestHandler` and 
    :class:`rasblite.engine.ModelParser`"""
    
    STARTING_DATA_MODES = ModelParser.STARTING_DATA_MODES # See ModelParser for info
    
    def __init__(self, model, data, port):
        """Initialises the Controller with the data model structure, starting data 
        and the port to stand up the HTTP server on.
        
        :param str model: format of the data model that will be built 
        :param str data: starting data to fill the model with (or a special string 
            that tells the Controller how to create the starting data
        :param int port: port to use for the HTTP server
        """
        
        self._raw_model       = model
        self._raw_data        = data
        self._port            = port
        self._server_address  = None
        
        self.__server_thread  = None
        self.__server         = None
        self.__model          = None
        
    def start(self):
        """Parses the model and fills it with starting data passed in at initialisation
        before standing up the HTTP server."""
        self.__parse_model()
        self.__start_server()
        
    def stop(self):
        """Stops the HTTP server, tearing it down and freeing any associated
        resources."""
        self.__stop_server()
        
    def is_server_running(self):
        """Returns True if the server and server thread is currently running, 
        otherwise False.
        
        :returns: True if the server is currently running
        :rtype: bool
        """
        return self.__server_thread.isAlive()
    
    def parse_response(self, raw_response):
        """Parses the response (HTTP body) into a Python collection, if applicable.
        For example, if the HTTP response body contained `<\html><h1>['a','b']</h1></html>`
        a Python :class:`list` would be returned with two elements, a and b.
        
        This function is useful because in the future the response from the 
        :class:`rasblite.engine.RequestHandler` may change to add extra info
        but this function will make sure external users are not impacted.
        
        :param bytes raw_response: raw bytes representing the HTTP body / payload
        :returns: decoded object from the raw response
        :rtype: str, list, dict (depending on raw_response)
        """
        return self.__server.RequestHandlerClass.parse_response(raw_response)
    
    def perform_user_request(self, method, path, message_body=None):
        """Carries out the user's instruction depending on the method (GET,POST,
        PUT or DELETE) and returns either the data requested or a 
        :class:`rasblite.engine.ModelData.ModelError` if there was an issue.
        
        :param str method: HTTP method used such as GET, POST, PUT or DELETE
        :param str path: full url requested by the user
        :param str message_body: data from the HTTP body (such as data to be put
            into the model)
        :returns: data requested by the user or a 
            :class:`rasblite.engine.ModelData.ModelError`
        :rtype: str, dict, list or :class:`rasblite.engine.ModelData.ModelError`
        """
        return self.__model.action_path(method, path, message_body)
        
    def __server_run_thread(self):
        """This method directly runs the HTTP server which is a blocking call and
        therefore is ran within a server thread.
        """
        try:
            print('Starting Server')
            self.__server.serve_forever()
            
            print('Confirmed, Server shutdown')
        except:
            print('ERROR: Failed to start server')
        finally:
            self.__server.server_close()
    
    def __start_server(self):
        """Creates a server thread using the port passed in at initialisation and
        then runs the thred which in turn stands up the HTTP server.
        """
        self._server_address = ('', self._port)
        self.__server = http.server.HTTPServer(self._server_address, RequestHandler)
        #Set ourselves onto the server so it can callback to us
        self.__server.RequestHandlerClass.set_controller(self)
        sa = self.__server.socket.getsockname()
        print("Serving HTTP on", sa[0], "port", sa[1], "...")
        
        self.__server_thread = Thread(target=self.__server_run_thread)
        self.__server_thread.start()
            
    def __stop_server(self):
        """Shutsdown the HTTP server and then waits for the server thread to close
        before returning."""
        print('Shutting down server...')
        self.__server.shutdown()
        self.__server_thread.join()
        print('Server shutdown')

            
    def __parse_model(self):
        """Creates a :class:`rasblite.engine.ModelParser` that parses the data 
        model and fills it with starting data if specified at initialisation.
        """
        model_parser = ModelParser()
        self.__model = model_parser.parse(self._raw_model, self._raw_data)
        pprint(self.__model)
        
        
