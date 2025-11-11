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
import random
from daemon.database import login_user
from daemon.weaprous import WeApRous

PORT = 8000  # Default port
TRACKER_PORT = 9000  # Default tracker port
PEER_PORT_RANGE = (9005, 9999)  # Random port range for peers

# Global data structures
# Peer connection management, has the format of {(ip, port): {ip: str, port: int, isUsed: bool, username: str}}
PEER_DICT = {} 

# Initialize the WeApRous application
app = WeApRous()

# Used for peer, to track connections and messages
peer_connections = {}

# Used for tracker, to track active peers
active_peers = []

# Used for tracker, to track channel messages
# Some channels are initially created
# Each key format: "channel_name": {"members": [List of peers], "messages": [List of messages in the channel]}
channel_messages = {
    "general": {"members": [], "messages": []},
    "random": {"members": [], "messages": []},
    "project": {"members": [], "messages": []},
    "help": {"members": [], "messages": []},
    "announcements": {"members": [], "messages": []},
}

# Used for peer, to track joined channels
# Format: ["channel1", "channel2", ...]
joined_channels = []

# Used for peer, to track received messages
received_messages = {} 

# Tracker server IP and port
# TRACKER_IP = None 
# TRACKER_IP = "192.168.1.26:8080"
# TRACKER_IP = "10.229.186.44:8080"

# ANSI color log helpers
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_GREEN = "\033[32m"
ANSI_BLUE = "\033[34m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

def log_error(msg, *args):
    print(f"{ANSI_RED}{ANSI_BOLD}[ERROR] {msg} {args}{ANSI_RESET}")

def log_warning(msg, *args):
    print(f"{ANSI_YELLOW}{ANSI_BOLD}[WARN] {msg} {args}{ANSI_RESET}")

def log_info(msg, *args):
    print(f"{ANSI_GREEN}{ANSI_BOLD}[INFO] {msg} {args}{ANSI_RESET}")

def log_debug(msg, *args):
    print(f"{ANSI_BLUE}{ANSI_BOLD}[DEBUG] {msg} {args} {ANSI_RESET}")

def register_tracker_routes(app):

    @app.route('/get-all-channels', methods=['GET'])
    def tracker_get_all_channels(headers, body):
        log_info(f"[Tracker] Get all channels called with headers: {headers} and body: {body}")
        # return_data = json.dumps(list(channel_messages.keys()))
        # return return_data
        return list(channel_messages.keys())
    
    @app.route('/join-channel', methods=['POST'])
    def tracker_join_channel(headers, body):
        '''
        Handle joining a channel via POST request.
        This route simulates a user joining a channel by printing the provided
        headers and body to the console.
        :param headers (str): The request headers or user identifier.
        :param body (str): The request body or channel information.
        format: "channel_name=general&peer_ip=127.0.0.1&peer_port=5000&username=alice"
        '''
        log_info(f"[Tracker] join-channel called with headers: {headers} and body: {body}")
        body = body.split('&')
        data = {}
        for item in body:
            key, value = item.split('=')
            data[key] = value

        channel_name = data.get('channel_name')
        ip = data.get('peer_ip')
        port = data.get('peer_port')
        username = data.get('username')

        if channel_name not in channel_messages:
            log_warning(f"[Tracker] Channel not found: {channel_name}")
            return {"status": "error", "message": "Channel not found"} 

        peer = {'ip': ip, 'port': port, 'username': username}
        if 'members' not in channel_messages[channel_name]:
            channel_messages[channel_name]['members'] = []
        if peer not in channel_messages[channel_name]['members']:
            channel_messages[channel_name]['members'].append(peer)
        log_info(f"[Tracker] Current channel members for {channel_name}: {channel_messages[channel_name]['members']}")
        return {"status": "success", "message": f"Joined channel {channel_name}"} 

    @app.route('/get-channel-messages', methods=['POST'])
    def tracker_get_channel_messages(headers, body):
        log_info(f"[Tracker] get-channel-messages called with headers: {headers} and body: {body}")
        body = body.split('&')
        data = {}
        for item in body:
            key, value = item.split('=')
            data[key] = value

        channel_name = data.get('channel_name')
        if channel_name not in channel_messages:
            log_warning(f"[Tracker] Channel not found: {channel_name}")
            return {"status": "error", "message": "Channel not found"} 
        return {"status": "success", "messages": channel_messages[channel_name]}
    
    @app.route('/send-channel-message', methods=['POST'])
    def tracker_send_channel_message(headers, body):
        log_info(f"[Tracker] send-channel-message called with headers: {headers} and body: {body}")
        body = body.split('&')
        data = {}
        for item in body:
            key, value = item.split('=')
            data[key] = value

        channel_name = data.get('channel_name')
        message = data.get('message')
        ip = data.get('peer_ip')
        port = data.get('peer_port')
        username = data.get('username')

        if channel_name not in channel_messages:
            log_warning(f"[Tracker] Channel not found: {channel_name}")
            return {"status": "error", "message": "Channel not found"}
        channel_messages[channel_name]['messages'].append({
            'sender_ip': ip,
            'sender_port': port,
            'username': username,
            'text': message
        })
        log_info(f"[Tracker] Message sent to {channel_name}: {message}")
        return {"status": "success", "message": f"Message sent to {channel_name}"}

    @app.route('/register-peer-pool', methods=['POST'])
    def register_peer_pool(headers, body):
        """
        Handle registration of a peer pool via POST request.

        This route simulates registering a pool of peers by printing the provided
        headers and body to the console.

        :param headers (str): The request headers or user identifier.
        :param body (str): The request body or peer pool data.
        """
        log_info(f"[Tracker] register-peer-pool called with headers: {headers} and body: {body}")
        body_split = body.split('&')
        peer = {}
        for item in body_split:
            key, value = item.split('=')
            peer[key] = value
        peer['isUsed'] = 0 

        # If the peer with the same IP and port already exists, return error
        if (peer['ip'], peer['port']) in PEER_DICT:
            log_warning(f"[Tracker] Peer already registered: {peer}")
            return False
        PEER_DICT[(peer['ip'], peer['port'])] = peer
        log_info(f"[Tracker] Current peer dict: {PEER_DICT}")
        return True
    """
    Register routes specific to the tracker role.
    """
    @app.route('/submit-info', methods=['POST'])
    def submit_info(headers, body):
        """
        Handle submission of user information via POST request.

        This route simulates tracking user information such as IP, port, username,. 
        It prints the provided information to the console.

        :param ip (str): The IP address of the user.
        :param port (str): The port number of the user.
        :param username (str): The username of the user.
        """
        log_info(f"[Tracker] submit-info called with headers: {headers} and body: {body}")
        body_split = body.split('&')
        info = {}
        for item in body_split:
            key, value = item.split('=')
            info[key] = value
        log_info(f"[Tracker] Received info: {info}")
        try:
            PEER_DICT[(info['ip'], info['port'])]['username'] = info['username']
            return True 
        except KeyError:
            log_warning(f"[Tracker] Peer not found for info submission: {info}")
            return False

    @app.route('/get-list', methods=['GET'])
    def get_list(headers, body):
        log_info(f"[Tracker] Get list called with headers: {headers} and body: {body}")
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

        log_info(f"[SampleApp] Login handle for user: {username} with password: {password}")
        log_info("Login status: ", login_user(username, password))
        if login_user(username, password):
            log_debug(PEER_DICT.items())
            for key, peer in PEER_DICT.items():
                if peer['isUsed'] == 0:
                    peer['isUsed'] = 1
                    peer_url = f"http://{peer['ip']}:{peer['port']}"
                    connection_ip = headers.get('x-connection-ip')
                    connection_port = headers.get('x-connection-port')

                    # Add the peer to the active peers list
                    active_peers.append(peer)

                    # if connection_ip is not None and connection_port is not None:
                    return {
                        'chosen_peer': peer,
                        'content_path': '/index.html',
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
    @app.route('/get-all-channels', methods=['GET'])
    def peer_get_all_channels(headers, body):
        log_info(f"[Peer] Get all channels called with headers: {headers} and body: {body}")
        s = socket.socket()
        s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1])))
        req = f"GET /get-all-channels HTTP/1.1\r\nHost: {TRACKER_IP}\r\n\r\n"
        s.sendall(req.encode())
        try:
            response = s.recv(4096).decode()
            body = response.split('\r\n\r\n', 1)[1] if '\r\n\r\n' in response else ''
            body = json.loads(body) if body else {}
            if 'channels' not in body:
                return None
            log_debug(f"[Peer] Received channel list: {body}")
            return body['channels']
        except socket.error:
            log_warning("[Peer] No response from tracker")
            return None
        finally:
            s.close()

    @app.route('/get-joined-channels', methods=['GET'])
    def peer_get_joined_channels(headers, body):
        log_info(f"[Peer] Get joined channels called with headers: {headers} and body: {body}")
        log_debug(f"[Peer] Joined channels: {joined_channels}")
        return joined_channels

    @app.route('/join-channel', methods=['POST'])
    def peer_join_channel(headers, body):
        log_info(f"[Peer] join-channel called with headers: {headers} and body: {body}")
        s = socket.socket()
        s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1]))) 
        channel_name = body.split('=')[1]
        global ip, port, username
        body = f"channel_name={channel_name}&peer_ip={ip}&peer_port={port}&username={username}"
        req = f"POST /join-channel HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        s.sendall(req.encode())
        try:
            response = s.recv(4096).decode()
            body = response.split('\r\n\r\n', 1)[1] if '\r\n\r\n' in response else ''
            body = json.loads(body) if body else {}
            log_debug(f"[Peer] Join channel response: {body}")
            if body.get('status') == 'success':
                joined_channels.append(channel_name)
            return body 
        except socket.error:
            log_warning("[Peer] No response from tracker")
            return {"status": "error", "message": "No response from tracker"}
        finally:
            s.close()

    @app.route('/get-channel-messages', methods=['POST'])
    def peer_get_channel_messages(headers, body):
        log_info(f"[Peer] get-channel-messages called with headers: {headers} and body: {body}")
        s = socket.socket()
        s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1]))) 
        channel_name = body.split('=')[1]
        body = f"channel_name={channel_name}"
        req = f"POST /get-channel-messages HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        s.sendall(req.encode())
        try:
            response = s.recv(4096).decode()
            body = response.split('\r\n\r\n', 1)[1] if '\r\n\r\n' in response else ''
            log_debug(f"[Peer] Get channel messages response: {body}")
            # return body 
            return json.loads(body) if body else {}
        except socket.error:
            log_warning("[Peer] No response from tracker")
            return {"status": "error", "message": "No response from tracker"}
        finally:
            s.close()
    
    @app.route('/send-channel-message', methods=['POST'])
    def peer_send_channel_message(headers, body):
        log_info(f"[Peer] send-channel-message called with headers: {headers} and body: {body}")
        s = socket.socket()
        s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1]))) 
        body = body.split('&')
        data = {}
        global ip, port, username
        for item in body:
            key, value = item.split('=')
            data[key] = value
        body = f"channel_name={data.get('channel_name')}&message={data.get('message')}&peer_ip={ip}&peer_port={port}&username={username}"
        req = f"POST /send-channel-message HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        s.sendall(req.encode())
        try:
            response = s.recv(4096).decode()
            body = response.split('\r\n\r\n', 1)[1] if '\r\n\r\n' in response else ''
            body = json.loads(body) if body else {}
            # if body.get('status') == 'success':
            #     if data.get('channel_name') in channel_messages:
            #         channel_messages[data.get('channel_name')].append(data.get('message'))
            log_debug(f"[Peer] Send channel message response: {body}")
            return body 
        except socket.error:
            log_warning("[Peer] No response from tracker")
            return {"status": "error", "message": "No response from tracker"}
        finally:
            s.close()

    @app.route('/submit-username', methods=['POST'])
    def submit_username(headers, body):
        """
        Handle submission of username via POST request.

        This route simulates submitting a username by printing the provided headers
        and body to the console.

        :param headers (str): The request headers or user identifier.
        :param body (str): The request body or username payload, formatted as "username=...".
        """
        global ip, port, username
        log_info(f"[Peer] submit-username called with headers: {headers} and body: {body}")
        _username = body.split('=')[1]
        body = f"ip={ip}&port={port}&username={_username}"
        log_info(f"[Peer] Username submitted: {_username}")
        req = f"POST /submit-info HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        try:
            s = socket.socket()
            s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1])))
            s.sendall(req.encode())
            s.close()
            username = _username
            return True
        except Exception as e:
            log_warning(f"[Peer] Error submitting username: {e}")
            return False

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

            # Remove peers that are already connected
            body = [peer for peer in body if (peer['ip'], int(peer['port'])) not in peer_connections]

            body = json.dumps(body)
            log_debug(f"[Peer] Received peer list: {body}")
            return body
        except socket.error:
            log_warning("[Peer] No response from tracker")
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
        log_info(f"[SampleApp] ['PUT'] Hello in {headers} to {body}")

    @app.route('/connect-peer', methods=['POST'])
    def connect_peer(headers, body):
        # Parse target IP and port from body (e.g., "ip=127.0.0.1&port=9002")
        log_info(f"[Peer] connect-peer called with headers: {headers} and body: {body}")
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
            log_debug(f"[Peer] connect-peer {headers=} {body=}")

    @app.route('/get-connected-peers', methods=['GET'])
    def get_connected_peers(headers, body):
        # Return list of connected peers
        peers = [{"ip": ip, "port": port} for (ip, port) in peer_connections.keys()]
        return json.dumps(peers)

    @app.route('/send-peer', methods=['POST'])
    def send_peer(headers, body):
        params = dict(x.split('=') for x in body.split('&'))
        target_ip = params.get('ip')
        target_port = int(params.get('port'))
        message = params.get('message', '')
        conn_key = (target_ip, target_port)
        header = f"POST /receive-message HTTP/1.1\r\nHost: {target_ip}:{target_port}\r\nContent-Length: {len(message)}\r\n\r\n"
        global ip, port, username
        body = {
            "message": message,
            "sender_ip": ip,
            "sender_port": port,
            "username": username
        }
        msg_data = header + json.dumps(body)
        try:
            s = peer_connections.get(conn_key)
            s.close()
            s = socket.socket()
            s.connect((target_ip, target_port))
            peer_connections[conn_key] = s
            s.sendall(msg_data.encode())
            return {"status": "success", "message": f"Sent to {target_ip}:{target_port}"}
        except Exception as e:
            return {"status": "error", "message": f"Cannot connect/send: {e}"}

    @app.route('/receive-message', methods=['POST'])
    def receive_message(headers, body):
        # Process and notify user of the incoming message
        log_info(f"[Peer] Received message: {body}")
        body = json.loads(body)
        sender_ip = body.get("sender_ip")
        sender_port = body.get("sender_port")
        log_info(f"[Peer] Message from {sender_ip}:{sender_port} - {body.get('message')}")
        # Optionally, store or push to UI
        # if (sender_ip, sender_port) not in received_messages:
        #     received_messages[(sender_ip, sender_port)] = []
        # received_messages[(sender_ip, sender_port)].append(body)
        received_messages[(sender_ip, sender_port)] = body
        return {"status": "success", "message": "Message received"}
    
    @app.route('/get-received-messages', methods=['GET'])
    def get_received_messages(headers, body):
        # Return all received messages
        # return json.dumps(received_messages)
            # Convert dict with tuple keys to a list of dicts for JSON serialization
        # formatted = []
        # for (sender_ip, sender_port), msgs in received_messages.items():
        #     for msg in msgs:
        #         entry = dict(msg)  # Copy the message dict
        #         entry['sender_ip'] = sender_ip
        #         entry['sender_port'] = sender_port
        #         formatted.append(entry)
        log_info(f"\033[1;32;43mAll received messages: {received_messages}\033[0m")
        formatted = []
        keys_to_remove = []
        for (sender_ip, sender_port), msg in received_messages.items():
            entry = dict(msg)
            entry['sender_ip'] = sender_ip
            entry['sender_port'] = sender_port
            formatted.append(entry)
            keys_to_remove.append((sender_ip, sender_port))
        # Remove after iteration
        for k in keys_to_remove:
            received_messages.pop(k)
        return json.dumps(formatted)
    
    @app.route('/broadcast-peer', methods=['POST'])
    def broadcast_peer(headers, body):
        body = json.loads(body)
        message = body.get("message", "")
        log_info(f"[Peer] Broadcasting message: {message}")
        if not message:
            return {"status": "error", "message": "No message to broadcast"}
        global ip, port
        body = {
            "message": message,
            "sender_ip": ip,
            "sender_port": port
        }
        errors = []
        for (peer_ip, peer_port), conn in peer_connections.items():
            try:
                conn.close()
                s = socket.socket()
                s.connect((peer_ip, peer_port))
                peer_connections[(peer_ip, peer_port)] = s
                conn = s
                header = f"POST /receive-message HTTP/1.1\r\nHost: {peer_ip}:{peer_port}\r\nContent-Length: {len(message)}\r\n\r\n"
                conn.sendall((header + json.dumps(body)).encode())
            except Exception as e:
                log_warning(f"[Peer] Error sending broadcast to {peer_ip}:{peer_port} - {e}")
                errors.append(f"Error sending to {peer_ip}:{peer_port} - {e}")
        if errors:
            return {"status": "error", "message": "; ".join(errors)}
        return {"status": "success", "message": "Broadcast sent"}

def register_with_tracker(tracker_ip, tracker_port, my_ip, my_port, username):
    """
    Register this peer with the tracker server.

    This function simulates the registration process by printing the registration
    details to the console. In a real implementation, it would send an HTTP request
    to the tracker server with the peer's information.
    """
    log_info(f"Registering with tracker at {TRACKER_IP}")
    s = socket.socket()
    s.connect((TRACKER_IP.split(':')[0], int(TRACKER_IP.split(':')[1])))
    body = f"ip={my_ip}&port={my_port}&username={username}"
    # req = f"POST /submit-info HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
    req = f"POST /register-peer-pool HTTP/1.1\r\nHost: {TRACKER_IP}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
    s.sendall(req.encode())
    try:
        log_info(s.recv(1024).decode())
    except socket.error:
        log_warning("[Peer] No response from tracker")
    s.close()

# if __name__ == "__main__":
#     # Parse command-line arguments to configure server IP and port
#     parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
#     parser.add_argument('--server-ip', default='0.0.0.0')
#     parser.add_argument('--server-port', type=int, default=PORT)
#     parser.add_argument('--role', choices=['tracker', 'peer'], default='peer')

#     args = parser.parse_args()
#     global ip, port, username
#     ip = args.server_ip
#     port = args.server_port
#     username = "n/a"

#     if args.role == 'tracker':
#         register_tracker_routes(app)
#         # Prepare and launch the RESTful application
#         app.prepare_address(ip, port)
#         app.run()
#     else:
#         register_peer_routes(app)
#         register_with_tracker(TRACKER_IP.split(':')[0], TRACKER_IP.split(':')[1], ip, port, "n/a")
#         # Prepare and launch the RESTful application
#         app.prepare_address(ip, port)
#         app.run()

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--host', default=None, help='Shared IP for both tracker and peer (e.g., 192.168.1.100)')
    parser.add_argument('--server-ip', default=None, help='Server bind IP (overrides --host)')
    parser.add_argument('--server-port', type=int, default=None, help='Server port (auto-generated for peer if not specified)')
    parser.add_argument('--tracker-port', type=int, default=TRACKER_PORT, help='Tracker port (default: 8080)')
    parser.add_argument('--tracker-ip', default=None, help='Full tracker address IP:PORT (overrides --host and --tracker-port)')
    parser.add_argument('--role', choices=['tracker', 'peer'], default='peer')

    args = parser.parse_args()
    global ip, port, username
    global TRACKER_IP
    
    # Determine server IP: priority is --server-ip > --host > '0.0.0.0'
    if args.server_ip:
        ip = args.server_ip
    elif args.host:
        ip = args.host
    else:
        ip = '127.0.0.1'
    
    # Determine server port based on role
    if args.role == 'tracker':
        port = args.server_port if args.server_port else args.tracker_port
    else:  # peer role
        if args.server_port:
            port = args.server_port
        else:
            # Auto-generate random port for peer
            port = random.randint(*PEER_PORT_RANGE)
            log_info(f"Auto-generated peer port: {port}")
    
    # Determine tracker address
    if args.tracker_ip:
        TRACKER_IP = args.tracker_ip
    elif args.host:
        TRACKER_IP = f"{args.host}:{args.tracker_port}"
    else:
        TRACKER_IP = f"127.0.0.1:{args.tracker_port}"
    
    username = "n/a"
    
    log_info(f"Role: {args.role}, Server IP: {ip}, Server Port: {port}")
    if args.role == 'peer':
        log_info(f"Tracker address: {TRACKER_IP}")

    if args.role == 'tracker':
        register_tracker_routes(app)
        # Prepare and launch the RESTful application
        app.prepare_address(ip, port)
        app.run()
    else:
        register_peer_routes(app)
        register_with_tracker(TRACKER_IP.split(':')[0], TRACKER_IP.split(':')[1], ip, port, "n/a")
        # Prepare and launch the RESTful application
        app.prepare_address(ip, port)
        app.run()