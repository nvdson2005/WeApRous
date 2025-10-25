#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse
from daemon.database import login_user
from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()

active_peers = []

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    body_split = body.split('&', 1)
    username = body_split[0].split('=')[1]
    password = body_split[1].split('=')[1]

    print("[SampleApp] Login handle for user: {} with password: {}".format(username, password))
    print("Login status: ", login_user(username, password))
    if login_user(username, password):
        connection_ip = headers.get('x-connection-ip')
        connection_port = headers.get('x-connection-port')
        if connection_ip is not None and connection_port is not None:
            submit_info(connection_ip, connection_port, username)
        else:
            print("[SampleApp] Missing connection IP/Port in headers")
            return {
            'content_path': '/login.html',
            'redirect': '/login.html',
            'set_cookie': 'auth=false'
            }
        return {
            'content_path': '/index.html',
            'redirect': '/index.html',
            'set_cookie': 'auth=true'
        }
    else:
        return {
            'content_path': '/login.html',
            'redirect': '/login.html',
            'set_cookie': 'auth=false'
        }
    # print("[SampleApp] Logging in {} to {}".format(headers, body))

@app.route('/submit-info', methods=['POST'])
def submit_info(ip, port, username):
    """
    Handle submission of user information via POST request.

    This route simulates tracking user information such as IP, port, username,
    and status. It prints the provided information to the console.

    :param ip (str): The IP address of the user.
    :param port (str): The port number of the user.
    :param username (str): The username of the user.
    :param status (str): The status of the user (e.g., 'online', 'offline').
    """
    print("[SampleApp] Submit info: IP={}, Port={}, Username={}".format(
        ip, port, username
    ))
    active_peers.append({
        'ip': ip,
        'port': port,
        'username': username
    })
    print("Current active peers: ", active_peers)

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    """
    Handle retrieval of the active peers list via GET request.

    This route returns the current list of active peers as a JSON response.

    :param headers (str): The request headers.
    :param body (str): The request body.
    :rtype: dict - A dictionary containing the list of active peers.
    """
    print("[SampleApp] Get list called with headers: {} and body: {}".format(headers, body))
    return_data = ""
    return_data = json.dumps(active_peers)
    return return_data

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()