#!/usr/bin/python

"""
SugarSync Linux client.

Usage:
    sugarsync.py --user <username> --password <password> --application <appId> --accesskey <publicAccessKey> --privatekey <privateAccessKey> ( quota | list | download <fileToDownload> | upload <fileToUpload> )
    sugarsync.py -h | --help
    sugarsync.py --version

Options:
    -u --user <username>                  SugarSync username (email address)
    -p --password <password>              SugarSync password
    -a --application <appId>              The id of the app created from developer site
       --accesskey <publicAccessKey>      Developer accessKey
       --privatekey <privateAccessKey>    Developer privateAccessKey
    <fileToDownload>                      The file from default "Magic Briefcase" folder that you want to download
    <fileToUpload>                        The file from current directory that you want to upload into default "Magic Briefcase" folder
    -h --help     Show this screen.
    --version     Show version.

Commands:
quota                 - Displays user quota
list                  - Lists "Magic Briefcase" folder contents
download "file.txt"   -  Downloads "file.txt" file  from "Magic Briefcase"
upload "file.txt"     - Uploads "file.txt" file  to "Magic Briefcase"
"""

# Main SugarSync Linux client file. It was written with python2.7 in mind.

from docopt import docopt   # docopt creates beautiful command-line interfaces
import xml.etree.ElementTree as ET
import os.path
import sys
import logging

#### for DEBUG ####
import urllib2
###################

# sugarsync packages:
from auth import RefreshToken, AccessToken
from utils import (XmlUtils, SugarSyncHTTPGetUtil, FileDownloadAPI,
                   FileCreation, FileUploadAPI)

ONE_GB = 1024.0 * 1024 * 1024


def handle_quota_command(user):
    """ Handles "quota" tool command. Takes a user instance and extracts from
    its info in xml format the quota information and displays it."""

    logger.debug("User info: \n" + user.xml_info.pprint())

    '''user xml info example: '''
    '''
    <?xml version="1.0" encoding="UTF-8"?>
    <user>
      ...
      <quota>
        <limit>2000000000</limit>
        <usage>345000000</usage>
      </quota>
      ...
    </user>
    '''
    limit = user.xml_info.get_node_values("./quota/limit")
    usage = user.xml_info.get_node_values("./quota/usage")

    storage_available_in_GB = int(limit) / ONE_GB
    storage_usage_in_GB = int(usage) / ONE_GB
    free_storage_in_GB = storage_available_in_GB - storage_usage_in_GB

    print("\n---QUOTA INFO---")
    print("Total storage available: {0:.3} GB".format(storage_available_in_GB))
    print("Storage usage: {0:.3} GB".format(storage_usage_in_GB))
    print("Free storage: {0:.3} GB \n".format(free_storage_in_GB))


def handle_list_command(user):
    """Handles "list" tool command. Makes an HTTP GET request to the
    user's "Magic Briefcase" contents link and displays the file and folder
    names within Magic Briefcase."""

    logger.debug("User info: \n" + user.xml_info.pprint())

    contents = get_magic_briefcase_contents(user)

    logger.debug("Magic Briefcase contents: \n" + contents.xml_info.pprint())

    print_folder_contents("MagicBriefcase", contents.xml_info)


def get_magic_briefcase_contents(user):
    '''
    Extracts the url to the Magic Briefcase resource, creates the url to
    the Magic Briefcase resource's contents and returns the response to
    that url.

    Info:
    Make an HTTP GET request to the URL that represents a collection
    resource to get information about the collection.
    Make an HTTP GET request to the URL that represents a collection's
    contents to list the collection's contents.
    '''

    # get the URL for magic briefcase collection resource from user info
    magic_briefcase_url = user.xml_info.get_node_values("./magicBriefcase")
    user.magic_briefcase = SugarSyncHTTPGetUtil(user.access_token,
                                                magic_briefcase_url)

    logger.debug("Magic Briefcase resource: \n" +
                 user.magic_briefcase.xml_info.pprint())

    # the URL that represents a collection's contents is obtained either by
    # appending /contents to the  URL that represents the collection:
#    magic_briefcase_url += '/contents'
    # or by reading the url from the xml response:
    contents_url = user.magic_briefcase.xml_info.get_node_values(".contents")
    # Make a HTTP GET request, GET because data keyword param is empty.
    user.magic_briefcase.contents = SugarSyncHTTPGetUtil(user.access_token,
                                                         contents_url)

    return user.magic_briefcase.contents


def print_folder_contents(collection_name, xml_resources):
    """Print folder contents."""

    folder_contents_template = ("-{0} \n\t"
                                "-Folders:"
                                "    {1} \n\t"
                                "-Files:"
                                "    {2} \n")
    folder_names, file_names = "", ""
    for folder in xml_resources.get_root_element().findall('./collection'):
        folder_names += "\n\t\t"
        folder_names += folder.find('displayName').text

    for file in xml_resources.get_root_element().findall('./file'):
        file_names += "\n\t\t"
        file_names += file.find('displayName').text

    print("\n\n")
    print(folder_contents_template.format(collection_name, folder_names,
                                          file_names))
    print("\n\n")


def handle_download_command(user, filename):
    """Issues an HTTP GET request to the data resource for the file."""

    logger.debug("User info: \n" + user.xml_info.pprint())
    # get the contents of Magic Briefcase as xml
    contents = get_magic_briefcase_contents(user)
    logger.debug("Magic Briefcase contents: \n" + contents.xml_info.pprint())

    files = contents.xml_info.get_root_element().findall('./file')
    # the following loop is time consuming, especially if there are hundreds
    # of files
    for file_resource in files:
        absolute_path = file_resource.find('./displayName').text
        # sometimes displayName contains the absolute path, but you
        # usually specify just the basename at the command line.
        # extract basename from path:
        name = os.path.basename(absolute_path)
        if filename == name:
            logger.info("file found")
            file_url = file_resource.find('./fileData').text
            downloader = FileDownloadAPI(user.access_token, file_url)
            downloader.download(filename)

            logger.info('\nDownload completed successfully. The {0} from '
                        '"MagicBriefcase" was downloaded to the '
                        'local directory.'.format(filename))
            return
    else:
        logger.info("File {0} not found in MagicBriefcase "
                    "folder.".format(filename))


def handle_upload_command(user, file):
    """Handles "upload" tool command.
    1. Extracts the "Magic Briefcase" folder link from the user object
    2. Creates a file representation in remote "Magic Briefcase" folder
    3. Uploads the file data associated to the previously created file
       representation"""

    if not os.path.exists(file):
        logger.info("\nFile {0} does not exist "
                    "in the current directory!".format(file))
        sys.exit()

    # get the URL for magic briefcase collection resource from user info
    magic_briefcase_url = user.xml_info.get_node_values("./magicBriefcase")
    file_representation = FileCreation(user.access_token, magic_briefcase_url)

    fileLink = file_representation.create_file(file, 'text/plain')
    logger.debug("File data link: %s" % fileLink)

    uploader = FileUploadAPI(user.access_token)
    response = uploader.upload_file(fileLink, file)
    logger.debug("response status %s" % response.status_code)

    logger.info('\nUpload completed successfully. Check "Magic Briefcase" '
                'remote folder')


### MAIN ####

# Create a beautiful CLI interface from the help string, in this case, __doc__
arguments = docopt(__doc__, version='SugarSync for Linux 0.1', help=True)

# same logger in all modules;
# .getLogger(name) retrieves the logger with name, creating it if necessary
logger = logging.getLogger('sugarsync')

# Retrieve the command line arguments:
username = arguments['--user']
password = arguments['--password']
application = arguments['--application']
access_key = arguments['--accesskey']
private_access_key = arguments['--privatekey']

"""
Get authentication tokens;
RefreshToken is persistent, but AccessToken isn't(about 1 hour)
RefreshToken exists so that the app doesn't need to store the user's
username & password for accessing user's resources
"""
refresh_token = RefreshToken(username, password, application,
                             access_key, private_access_key).token
access_object = AccessToken(access_key, private_access_key, refresh_token)
access_token = access_object.token
user_url = XmlUtils(access_object.response_body).get_node_values("./user")

user = SugarSyncHTTPGetUtil(access_token, user_url)

## DEBUG ##
logger.debug('Refresh Token: ' + refresh_token)
logger.debug('Access Token: ' + access_token)
logger.debug('Response to request for access token: \n' +
             XmlUtils(access_object.response_body).pprint())
###########

if arguments['quota']:
    logger.info('"Quota" command chosen.')
    handle_quota_command(user)
elif arguments['list']:
    logger.info('"List" command chosen.')
    handle_list_command(user)
elif arguments['download']:
    file = arguments['<fileToDownload>']
    logger.info('"Download {0}" command chosen.'.format(file))
    handle_download_command(user, file)
elif arguments['upload']:
    file = arguments['<fileToUpload>']
    logger.info('"Upload {0}" command chosen.'.format(file))
    handle_upload_command(user, file)
else:
    # it will never get here because docopt takes care of that;
    # this is left for future extension
    logger.info('Unknown command')

logger.info("sugarsync.py end")
###########
