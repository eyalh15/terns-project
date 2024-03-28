import re
import base64
import sys
import argparse
import requests

from requests.auth import HTTPDigestAuth

CAM_IP = '2.55.92.58'
## south camera
CAM_PORT_S = '8080'
## north camera
CAM_PORT_N = '9090'
USER_NAME = 'admin'
PASSWORD = 'rt121271'


## Create different URL for the south and north cameras
def URL_S_N(location):
    ## location can be south or north
    if location == "south":
        url = 'http://' + USER_NAME + ':' + PASSWORD + '@' + CAM_IP + ':' + CAM_PORT_S + '/cgi-bin/ptz.cgi'
    elif location == "north":
        url = 'http://' + USER_NAME + ':' + PASSWORD + '@' + CAM_IP + ':' + CAM_PORT_N + '/cgi-bin/ptz.cgi'

    return (url)


# url = 'http://' + USER_NAME + ':' + PASSWORD + '@' + CAM_IP + ':' + CAM_PORT + '/cgi-bin/ptz.cgi'


auth = HTTPDigestAuth(USER_NAME, PASSWORD)


def getPTZValues(location):
    # print('Commanding: ' + url + '?action=getStatus')

    session = requests.Session()
    session.auth = (USER_NAME, PASSWORD)
    url = URL_S_N(location)
    print (url)
    response = session.get(url + '?action=getStatus', auth=HTTPDigestAuth(USER_NAME, PASSWORD))


    return (response)
"""
    # Define the regular expression pattern to match status.Postion[index]=value
    pattern = r'status\.Postion\[(\d+)\]=(.*)'
    matches = re.findall(pattern, response.text)

    positions = {}
    # Iterate over the matches and extract positions values
    for match in matches:
        index = int(match[0])
        value = float(match[1])
        positions[index] = value
    print(f'Current PTZ values - ({positions[0]}, {positions[1]}, {positions[2]})')
    return (positions[0], positions[1], positions[2])
"""
try_1=getPTZValues("north")

print (try_1.text)