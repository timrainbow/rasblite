#!/usr/bin/env python3
""" 
This run script gives a command line entry point to the core rasblite module. It
is designed to be ran by the user from the command line but it can also be used
to quickly stand up a configured server from a bash script for example. 
"""
import argparse
import os
import sys

# If the user hasn't installed rasblite then try to find it in this repo.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from rasblite import engine

def add_parser_arguments(arg_parser):
    """Adds arguments to the :class:`argparse.ArgumentParser` which is passed in
    to allow the user to configure rasblite.
    
    :param argparse.ArgumentParser arg_parser: argument parser to add arguments to
    :returns: Argument parser which was originally passed in
    :rtype: argparse.ArgumentParser
    
    """
    arg_parser.add_argument('--model', '-m', type=argparse.FileType('r'), required=True)
    arg_parser.add_argument('--starting_data', '-d', type=str)
    arg_parser.add_argument('--port', '-p', type=int, default=8080)
    
    
    return arg_parser

def parse_command_line():
    """Creates an :class:`argparse.ArgumentParser` and parses the arguments passed
    on the command line. These arguments as well as the error function for the 
    :class:`argparse.ArgumentParser` are then returned.
    
    :returns: arguments -- arguments parsed from the command line 
    :returns: error_function -- :class:`argparse.ArgumentParser` error_function.
    
    """
    arg_parser = argparse.ArgumentParser(description='Lightweight RESTful API Server Builder Command Line Tool')
    arg_parser = add_parser_arguments(arg_parser)
    
    return (arg_parser.parse_args(), arg_parser.error)

def expand_arguments(args, error_function):
    """Puts the arguments passed on the command line into a dictionary so that 
    the dictionary can be expanded and passed to a function expecting. Also 
    verifies the arguments such as checking filepaths exist.
    
    :param args: arguments parsed by :class:`argparse.ArgumentParser`
    :param error_function: :class:`argparse.ArgumentParser` error function
    :returns: dictionary containing the arguments passed on the command line
    :rtype: dict
    
    """
    expanded_args = {}
    
    starting_data = args.starting_data
    if args.starting_data not in engine.Controller.STARTING_DATA_MODES:
        if os.path.exists(starting_data) and os.path.isfile(starting_data):
            starting_data = open(args.starting_data, 'r').read()
        else:
            error_function("Could not read file: " + starting_data 
                             + ". Did you mean to use a defined type? (" 
                             + ", ".join(engine.Controller.STARTING_DATA_MODES.keys()) + ")")
                
    
    # Get args   
    expanded_args['data']  = starting_data
    expanded_args['model'] = args.model.read()
    expanded_args['port']  = args.port
    
    # Clean up!
    args.model.close()

    return expanded_args

        
def main(model, data, port):
    """The entry point for running rasblite module, mainly for when this script
    is called from the command line. Another Python script probably would not want
    to call this unless it was extending the functionality of it. Otherwise it
    would be better to call the :class:`rasblite.engine.Controller` directly.
    
    :param str model: format of the data model that will be built 
    :param str data: starting data to fill the model with (or a special string 
        that tells rasblite how to create the starting data
    :param int port: port to use for the HTTP server
    
    """
    print('RASBLite Start!')
    controller = engine.Controller(model, data, port)
    
    try:
        controller.start()
        input('Press ENTER to exit...')
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        controller.stop()

def command_line_run():
    """Parses the command line before passing the arguments to the main function"""
    args, error_function = parse_command_line()
    main(**expand_arguments(args, error_function))
    print('Exiting...')
    
if __name__ == '__main__':
    """Hook to command line run."""
    command_line_run()
