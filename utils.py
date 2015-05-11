#!/usr/bin/python

"""Contains utility classes needed for parsing XML, etc."""

import xml.etree.ElementTree as ET        # convert to and from XML
import xml.dom.minidom      # a light-weight implementation of the DOM i-face
import urllib2                            # open urls
import requests             # replaces urllib2, HTTP for Humans
import logging             

def make_request(http_request):
        """Makes the actual HTTP request and gets a HTTP response, handling 
        any exceptions."""
       
        try:
            """
            urllib2 uses httplib which uses the socket module.
            By default the socket module has no timeout and can hang. So you 
            should specify how long a socket should wait for a response before 
            timing out.
            """
            response = urllib2.urlopen(http_request)
        except urllib2.HTTPError as e:
            logger.debug("The server couldn't fulfill the request.")
            logger.debug('Error code: ', e.code)
            # If we get a redirect, the URL of the page fetched may not be 
            # the same as the URL requested, so we need the real url:
            logger.debug("The actual URL you got the response from:")
            logger.debug(e.geturl()) 
            logger.debug("Here are the response headers:")
            logger.debug(e.info())
            logger.debug("Response body, usually HTML format:")              
            logger.debug(e.read())               # reads the HTML page with the error
        except urllib2.URLError as e:
            logger.error("We failed to reach a server.")
            logger.error("Reason: ", e.reason)
        else: 
            logger.debug("Got response from server!")

            return response    # obj. with .geturl(), .read(), .info() methods
        

class XmlUtils(object):
    '''Used to parse XML files.'''
    def __init__(self, xml_string):
        self.xml_string = xml_string
        # Parse XML tree into an Element with Element nodes
        self.root = ET.fromstring(self.xml_string)      # the top most Element
        
    def pprint(self):
        '''Makes self.xml_string readable for sys.stdout or other streams.'''
        xml_doc = xml.dom.minidom.parseString(self.xml_string)
        pretty_xml_as_string = xml_doc.toprettyxml()
        return pretty_xml_as_string
    
    def get_node_values(self, path_string):
        ''' Extracts node values using XPath expressions.
        write the docstring. 
        '''
        return self.root.find(path_string).text
    
    def get_root_element(self):
        '''Useful when you need to extract info from an XML Elmenent using
        methods like .findall() or .find(), etc.'''
        return self.root
       
        

class SugarSyncHTTPGetUtil(object):
    """Sample class used for making HTTP GET requests. Children should
    override run()."""
    
    # The User-Agent HTTP Request header's value 
    user_agent = "SugarSync API Sample/1.0"
    
    def __init__(self, access_token, url):
        '''Sets the headers for the user info request and makes the request.'''
        
        self.access_token = access_token
        self.url = url
        # Create the HTTP headers
        self.headers = { 'User-Agent' : self.user_agent,
                         'Authorization' : access_token }
        self.run()
        
    def run(self):
        '''Calls the methods in an immutable order.'''
        self.make_get_request(self.url)
        self.get_info()
        self.get_xml_info()
   
    def make_get_request(self, url):
        """Make a HTTP GET request, GET because data keyword param is 
        empty."""
        self.request = urllib2.Request(url, headers=self.headers)
        self.response = make_request(self.request)
        return self.response
    
    def get_info(self):
        '''Returns the HTTP response message body.'''
        self.info = self.response.read()
        # next time you call .read() on the same response, it will return 
        # nothing
        return self.info     
 
    def get_xml_info(self):
        '''Returns the user info as an XML Element that can be parsed.'''
        
        self.xml_info = XmlUtils(self.info)
        return self.xml_info
    

class FileDownloadAPI(SugarSyncHTTPGetUtil):
    """Sample class for file download."""
    
    def run(self):
        '''Calls the methods in an immutable order. Overrides 
        the parent's run(). It is being called by __init__().'''
        
        self.make_get_request(self.url)
        self.get_info()
    
    def download(self, filename):
        """Writes the downloaded data to the local file."""

        with open(filename, 'wb') as stream:       # open(filename_or_a_path)
            downloaded_file = stream.write(self.info)  


"""When you upload a file, first you create the file in the target folder, 
then you upload your local data to that file."""

class FileCreation():
    """Sample class used for creating a file representation. Note that the 
    file data must be uploaded using a different api."""
    
    # The User-Agent HTTP Request header's value 
    USER_AGENT = "SugarSync API Sample/1.0"
    
    # template used for creating a file representation:
    CREATE_FILE_REQUEST_TEMPLATE = ('<?xml version="1.0" encoding="UTF-8" ?>'
                                        "<file>"
                                                "<displayName>{0}</displayName>"
                                                "<mediaType>{1}</mediaType>"
                                        "</file>")

    def __init__(self, access_token, url):
        '''Sets the headers for the user info request and makes the request.'''
        
        self.access_token = access_token
        self.url = url
        # Create the HTTP headers
        self.headers = { 'User-Agent' : self.USER_AGENT,
                         'Content-Type' : "application/xml; charset=UTF-8",
                         'Authorization' : access_token }
          
    def create_file(self, display_name, media_type):  
        '''Calls the methods in an immutable order. It replaces .run()'''
        
        self.template = self.fill_template(display_name, media_type)
        self.make_post_request(self.url, self.template)

        self.headers = self.response.info()
        # get the location of the file:
        self.fileLink = self.headers.get('Location', '')
        if self.fileLink == '':
            raise ValueError("File link is empty!")
        # Get the location of the file data:
        self.fileLink += '/data'
        
        return self.fileLink 
    
    def make_post_request(self, url, data=None):
        """Make a HTTP POST request, like GET but with data keyword param 
        not empty."""
        
        self.request = urllib2.Request(url, data=data, headers=self.headers)
        self.response = make_request(self.request)
        return self.response
    
    def fill_template(self, display_name, media_type):
        '''Fills CREATE_FILE_REQUEST_TEMPLATE with display_name & media_type.'''
        
        return self.CREATE_FILE_REQUEST_TEMPLATE.format(display_name,
                                                        media_type)


class FileUploadAPI(object):
    '''Sample class for uploading a file.'''
    
    API_SAMPLE_USER_AGENT = "SugarSync API Sample/1.0"
    
    def __init__(self, access_token):
        self.headers = {'User-Agent' : self.API_SAMPLE_USER_AGENT,
                        'Content-Type': 'application/octet-stream; charset=UTF-8',
                        'Authorization': access_token}
    
    def upload_file(self, file_data_url, local_file_path):
        stream = open(local_file_path, 'rb')    # open(filename_or_a_path)
        data = stream.read()                    # read until EOF
        self.headers['Content-Length'] = str(len(data))
        self.response = requests.put(file_data_url, data=data, headers=self.headers)
        
        return self.response
 
 
def get_logger(name, file):
    '''Initialization; this is used to create any loggers needed. '''
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)    
    # if level = INFO, records all except DEBUG
    
    # Handlers send the log records (created by loggers) to the appropriate 
    # destination: a console, a file, over the internet, by email, etc.
    # create a file handler, overriding the default StreamHandler:
    fh = logging.FileHandler(filename=file, mode='w')
    fh.setLevel(logging.DEBUG)
    console = logging.StreamHandler()              # stream = sys.stdout
    console.setLevel(logging.INFO)
    
    # Formatters specify the layout of log records in the final output:
    formatter = logging.Formatter(fmt='%(asctime)s %(filename)s %(funcName)s ' +
                    '%(levelname)s %(message)s')   
    # http://docs.python.org/2/library/logging.html#logrecord-attributes
    fh.setFormatter(formatter)
    console.setFormatter(formatter)
    
    # a logger can have multiple handlers, each with its own log level
    logger.addHandler(fh)
    logger.addHandler(console)
    
    return logger    


##### MAIN #####

# logger initialization, the same logger in all modules, any modules that 
# import this module will have access to this logger: 
logger = get_logger('sugarsync', 'sugarsync.log')
