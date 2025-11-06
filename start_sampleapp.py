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

PEER_DICT = {} 
app = WeApRous()

peer_connections = {}
active_peers = []
received_messages = {} 

TRACKER_IP = "127.0.0.1:8080"

def register_tracker_routes(app):
    @app.route('/register-peer-pool', methods=['POST'])
    def register_peer_pool(headers, body):
        """
        Handle registration of a peer pool via POST request.

        This route simulates registering a pool of peers by printing the provided
        headers and body to the console.

        :param headers (str): The request headers or user identifier.
        :param body (str): The request body or peer pool data.
        """
        print("[Tracker] register-peer-pool called with headers: {} and body: {}".format(headers, body))
        body_split = body.split('&')
        peer = {}
        for item in body_split:
            key, value = item.split('=')
            peer[key] = value
        peer['isUsed'] = 0 

        # If the peer with the same IP and port already exists, return error
        if (peer['ip'], peer['port']) in PEER_DICT:
            print("[Tracker] Peer already registered: {}".format(peer))
            return False
        PEER_DICT[(peer['ip'], peer['port'])] = peer
        print("[Tracker] Current peer dict: {}".format(PEER_DICT))
        return True
    """
    Register routes specific to the tracker role.
    """
    @app.route('/submit-info', methods=['POST'])
    def submit_info(headers, body):
        """
        Handle submission of user information via POST request.

        This route simulates tracking user information such as IP, port, username,
        and status. It prints the provided information to the console.

        :param ip (str): The IP address of the user.
        :param port (str): The port number of the user.
        :param username (str): The username of the user.
        :param status (str): The status of the user (e.g., 'online', 'offline').
        """
        print("[Tracker] submit-info called with headers: {} and body: {}".format(headers, body))
        body_split = body.split('&')
        info = {}
        for item in body_split:
            key, value = item.split('=')
            info[key] = value
        active_peers.append(info)
        print("[Tracker] Current active peers: {}".format(active_peers))
        return True 

    @app.route('/get-list', methods=['GET'])
    def get_list(headers, body):
        print("[Tracker] Get list called with headers: {} and body: {}".format(headers, body))
        return_data = json.dumps(active_peers)
        return return_data

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
            print(PEER_DICT.items())
            for key, peer in PEER_DICT.items():
                if peer['isUsed'] == 0:
                    peer['isUsed'] = 1
                    peer_url = f"http://{peer['ip']}:{peer['port']}"
                    connection_ip = headers.get('x-connection-ip')
                    connection_port = headers.get('x-connection-port')

                    # Add the peer to the active peers list
                    active_peers.append(peer)

                    # if connection_ip is not None and connection_port is not None:
                    #     submit_info(connection_ip, connection_port, username)
                    # else:
                    #     print("[SampleApp] Missing connection IP/Port in headers")
                    #     return {
                    #     'content_path': '/login.html',
                    #     # 'redirect': '/login.html',
                    #     'redirect': peer_url,
                    #     'set_cookie': 'auth=false'
                    #     }
                    return {
                        'chosen_peer': peer,
                        'content_path': '/index.html',
                        # 'redirect': '/index.html',
                        'redirect': peer_url,
                        'set_cookie': 'auth=true'
                    }
            return {
                'chosen_peer': None,
            }
        else:
            return {
                'content_path': '/login.html',
                'redirect': '/login.html',
                'set_cookie': 'auth=false'
            }
        # print("[SampleApp] Logging in {} to {}".format(headers, body))

def register_peer_routes(app):
    @app.route('/get-list', methods=['GET'])
    def get_list(headers, body):
        """
        Handle retrieval of the active peers list via GET request.

        This route returns the current list of active peers as a JSON response.

        :param headers (str): The request headers.
        :param body (str): The request body.
        :rtype: dict - A dictionary containing the list of active peers.
        """
        s = socket.socket()
        s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1])))
        req = f"GET /get-list HTTP/1.1\r\nHost: {TRACKER_IP}\r\n\r\n"
        s.sendall(req.encode())
        try:
            response = s.recv(4096).decode()
            body = response.split('\r\n\r\n', 1)[1] if '\r\n\r\n' in response else ''
            body = json.loads(body) if body else []

            # Remove self from the peer list
            global ip, port # Get the current peer's IP and port (cannot get from headers as it is from the requester)
            body = [peer for peer in body if not (peer['ip'] == ip and int(peer['port']) == port)]

            body = json.dumps(body)
            print("[Peer] Received peer list: ", body)
            return body
        except socket.error:
            print("[Peer] No response from tracker")
            return "[]"
        finally:
            s.close()

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

    @app.route('/connect-peer', methods=['POST'])
    def connect_peer(headers, body):
        # Parse target IP and port from body (e.g., "ip=127.0.0.1&port=9002")
        print(f"[Peer] connect-peer called with headers: {headers} and body: {body}")
        params = dict(x.split('=') for x in body.split('&'))
        target_ip = params.get('ip')
        target_port = int(params.get('port'))
        try:
            s = socket.socket()
            s.connect((target_ip, target_port))
            peer_connections[(target_ip, target_port)] = s
            return {"status": "success", "message": f"Connected to {target_ip}:{target_port}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            print(f"[Peer] connect-peer {headers=} {body=}")

    @app.route('/get-connected-peers', methods=['GET'])
    def get_connected_peers(headers, body):
        # Return list of connected peers
        peers = [{"ip": ip, "port": port} for (ip, port) in peer_connections.keys()]
        return json.dumps(peers)

    @app.route('/send-peer', methods=['POST'])
    def send_peer(headers, body):
        # Expect body: "ip=127.0.0.1&port=9002&message=Hello"
        params = dict(x.split('=') for x in body.split('&'))
        target_ip = params.get('ip')
        target_port = int(params.get('port'))
        message = params.get('message', '')
        conn_key = (target_ip, target_port)
        header = f"POST /receive-message HTTP/1.1\r\nHost: {target_ip}:{target_port}\r\nContent-Length: {len(message)}\r\n\r\n"
        body = {
            "message": message,
            "sender_ip": headers.get('x-connection-ip'),
            "sender_port": headers.get('x-connection-port')
        }
        message = header + json.dumps(body)
        try:
            s = peer_connections.get(conn_key)
            if not s:
                return {"status": "error", "message": "No connection to target peer"}
            # Send message as simple text (could use a protocol)
            s.sendall(message.encode())
            return {"status": "success", "message": f"Sent to {target_ip}:{target_port}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            print(f"[Peer] send-peer {headers=} {body=}")

    @app.route('/receive-message', methods=['POST'])
    def receive_message(headers, body):
        # Process and notify user of the incoming message
        print(f"[Peer] Received message: {body}")
        body = json.loads(body)
        sender_ip = body.get("sender_ip")
        sender_port = body.get("sender_port")
        print(f"[Peer] Message from {sender_ip}:{sender_port} - {body.get('message')}")
        # Optionally, store or push to UI
        received_messages[(sender_ip, sender_port)] = body
        return {"status": "success", "message": "Message received"}
    
    @app.route('/get-received-messages', methods=['GET'])
    def get_received_messages(headers, body):
        # Return all received messages
        return json.dumps(received_messages)
    
    @app.route('/broadcast-peer', methods=['POST'])
    def broadcast_peer(headers, body):
        message = body.get("message", "")
        for (peer_ip, peer_port), conn in peer_connections.items():
            if conn:
                try:
                    header = f"POST /receive-message HTTP/1.1\r\nHost: {peer_ip}:{peer_port}\r\nContent-Length: {len(message)}\r\n\r\n"
                    body = {
                        "message": message,
                        "sender_ip": headers.get('x-connection-ip'),
                        "sender_port": headers.get('x-connection-port')
                    }
                    conn.sendall((header + json.dumps(body)).encode())
                except Exception as e:
                    print(f"[Peer] Error sending broadcast to {peer_ip}:{peer_port} - {e}")
        return {"status": "success", "message": "Broadcast sent"}

    @app.route('/broadcast-peer', methods=['POST'])
    def broadcast_peer(headers, body):
        # TODO: send to all connected peers
        print(f"[Peer] broadcast-peer {headers=} {body=}")
    

def register_with_tracker(tracker_ip, tracker_port, my_ip, my_port, username):
    """
    Register this peer with the tracker server.

    This function simulates the registration process by printing the registration
    details to the console. In a real implementation, it would send an HTTP request
    to the tracker server with the peer's information.
    """
    print(tracker_ip, tracker_port, my_ip, my_port, username)
    print(f"[Peer] Registering with tracker at {TRACKER_IP}")
    s = socket.socket()
    s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1])))
    body = f"ip={my_ip}&port={my_port}&username={username}"
    # req = f"POST /submit-info HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
    req = f"POST /register-peer-pool HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
    s.sendall(req.encode())
    try:
        print(s.recv(1024).decode())
    except socket.error:
        print("[Peer] No response from tracker")
    s.close()

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
    parser.add_argument('--role', choices=['tracker', 'peer'], default='peer')

    args = parser.parse_args()
    global ip, port
    ip = args.server_ip
    port = args.server_port

    if args.role == 'tracker':
        register_tracker_routes(app)
        # Prepare and launch the RESTful application
        app.prepare_address(ip, port)
        app.run()
    else:
        register_peer_routes(app)
        register_with_tracker(TRACKER_IP.split(':')[0], TRACKER_IP.split(':')[1], ip, port, "peer1")
        # Prepare and launch the RESTful application
        app.prepare_address(ip, port)
        app.run()