#!/usr/bin/python

# This script is part of a SugarSync Linux client and handles authentication.

# Normal flow for authentication:
#    user credentials(formatted as XML) are sent by a HTTP Post method as a
#    request for a Refresh Token.
#    using the Refresh Token you request by HTTP Post an Access Token which
#    grants access to the user's resources.
#    
# Along with the Access Token, received as an HTTP response header, you get
# the URL to the user's resources.

# Here are defined the classes that create the Refresh Token and Access Token.

import urllib         # Open arbitrary resources by URL  
import urllib2        # basic and digest authentication, redirections, cookies  

# sugarsync packages:   
import utils


class TokenFactory(object):
    '''Parent class for RefreshToken and AccessToken. The procedure for 
    creating a token is the same, only the API's url, user agent and
    xml request string differ.'''
    
    def __init__(self, object):
        self.response = self.get_authorization_response(object)
        self.response_url = self.response.geturl()
        self.response_headers = self.response.info()         
        # response_headers is a dictionary-like object
        
        # response is a file-like object with .read(), etc. but
        # .read() returns data only once per same object 
        self.response_body = self.response.read()    

        self.token = self.response_headers.get('Location', '')
    
    def get_authorization_response(self, object):
        '''Defines the HTTP POST request to SugarSync's API and returns a 
        HTTP Response. Normally, object should be a child class.'''
        
        url = object.URL
        # Create the HTTP headers
        headers = { 'User-Agent' : object.USER_AGENT,
                    'Content-Type' : "application/xml; charset=UTF-8" }
        '''If you are serving up XML as the message body without doing any 
        other encoding on it, then you probably want application/xml.'''
        
        # Make a request using HTTP POST because data keyword param. is not 
        # empty, if data is empty => GET request
        self.request = urllib2.Request(url, data=object.data, headers=headers)
        response = utils.make_request(self.request)
        
        return response
        

class RefreshToken(TokenFactory):
    '''Sample code used for getting a refresh token.'''
    
    # SugarSync App Authorization API url
    URL = "https://api.sugarsync.com/app-authorization"
    
    # The User-Agent HTTP Request header's value 
    USER_AGENT = "SugarSync API Sample/1.1"
        
    # The template used for creating the request, as an implicitly joined str
    template = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<appAuthorization>'
                     '<username>{0}</username>'
                     '<password>{1}</password>'
                     '<application>{2}</application>'
                     '<accessKeyId>{3}</accessKeyId>'
                     '<privateAccessKey>{4}</privateAccessKey>'
                '</appAuthorization>')

    """WHERE:     
    username - SugarSync username (email address)
    password - SugarSync password
    application - The app id of a previously created app
    accessKey - Developer application accessKey
    privateAccessKey - Developer application privateAccessKey
    {*} - variable placeholder when using APP_AUTH_REQUEST_TEMPLATE.format(vars...)
    """
    
    def __init__(self, *args):
        '''Fills the template unique to this class with the request details: 
        replaces "{ }" from the template with arguments and calls
        other helper methods.
        Cannot return anything, otherwise you get a Type error at runtime.'''
        
        self.data = self.template.format(*args)
        # To use super(), it needs to inherit from object, directly or not
        # All the classes that inherit from object are new style, 
        # classes >=python2.2
        super(RefreshToken, self).__init__(self)
        
        
class AccessToken(TokenFactory):
    '''Sample code used for getting access tokens using a refresh token.
    Multiple access tokens can be obtained from the same refresh token.
    They last for almost an hour and grant access to user's resources.
    With an access token there is no need to store the user's credentials.'''
    
    # SugarSync Access Token API url
    URL = "https://api.sugarsync.com/authorization"
    # The User-Agent HTTP Request header's value
    USER_AGENT = "SugarSync API Sample/1.0"
    # The template used for creating the request
    template = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<tokenAuthRequest>'
                    '<accessKeyId>{0}</accessKeyId>'
                    '<privateAccessKey>{1}</privateAccessKey>'
                    '<refreshToken>{2}</refreshToken>'
                '</tokenAuthRequest>')
    """WHERE:     
    accessKey - Developer application accessKey
    privateAccessKey - Developer application privateAccessKey
    refreshToken - token obtained using the user's username & password
    """
    def __init__(self, *args):
        self.data = self.template.format(*args)
        # Call the parent class __init__ with itself as argument
        super(AccessToken, self).__init__(self)



if __name__ == '__main__':
    print("This file should not be used directly, it is used by sugarsync.py.")