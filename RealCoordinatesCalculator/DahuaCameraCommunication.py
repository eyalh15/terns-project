"""
This module contains HTTP requests to command and fetch data from Dahua camera.
"""

import re
import requests
import configparser
from requests.auth import HTTPDigestAuth

# Load configuration from ini file
config = configparser.ConfigParser()
config.read('get_camera_ptz.ini')  # Make sure this file exists in the same directory

CAM_IP = config.get('General', 'CAM_IP')
CAM_PORT = config.get('General', 'CAM_PORT')
USER_NAME = config.get('General', 'USER_NAME')
PASSWORD = config.get('General', 'PASSWORD')

## Create different URL for the south and north cameras
def create_url():
    return 'http://' + USER_NAME + ':' + PASSWORD + '@' + CAM_IP + ':' + CAM_PORT + '/cgi-bin/ptz.cgi'


auth = HTTPDigestAuth(USER_NAME, PASSWORD)

def getPTZValues():
    session = requests.Session()
    session.auth = (USER_NAME, PASSWORD)
    url = create_url()

    response = session.get(url + '?action=getStatus', auth=HTTPDigestAuth(USER_NAME, PASSWORD))

    # Define the regular expression pattern to match status.Postion[index]=value
    pattern = r'status\.Postion\[(\d+)\]=(.*)'
    matches = re.findall(pattern, response.text)

    positions = {}
    # Iterate over the matches and extract positions values
    for match in matches:
        index = int(match[0])
        value = float(match[1])
        positions[index] = value

    return (positions[0], positions[1], positions[2])

    