# WeApRous - P2P Chat Application

## Project Overview

WeApRous is a peer-to-peer (P2P) chat application built with a custom HTTP server framework. The application supports both direct peer-to-peer messaging and channel-based group chat functionality. It consists of three main components:

1. **Tracker Server**: Central server that manages peer registration, channel management, and message routing
2. **Peer Server**: Individual peer nodes that can connect to other peers and participate in channels
3. **Proxy Server**: HTTP reverse proxy that routes requests to appropriate backend servers

## Architecture

The application follows a client-server architecture with P2P capabilities:

- **Tracker**: Manages peer pool, channels, and coordinates peer connections
- **Peers**: Connect to tracker, register themselves, and communicate with other peers
- **Proxy**: Routes HTTP requests based on hostname to appropriate backend servers

## Project Structure

```
WeApRous/
├── daemon/              # Core framework modules
│   ├── __init__.py      # Package initialization and exports
│   ├── backend.py       # Backend server implementation
│   ├── database.py      # User authentication database
│   ├── dictionary.py    # Case-insensitive dictionary utilities
│   ├── httpadapter.py   # HTTP request/response adapter
│   ├── proxy.py         # Proxy server implementation
│   ├── request.py       # HTTP request parsing
│   ├── response.py      # HTTP response building
│   ├── utils.py         # Utility functions
│   └── weaprous.py      # WeApRous web framework
├── apps/                # Application modules
│   └── sampleApp.py    # Sample application example
├── config/              # Configuration files
│   └── proxy.conf       # Proxy server configuration
├── db/                  # Database files
│   └── database.csv     # User credentials database
├── static/              # Static assets
│   ├── css/
│   │   └── styles.css   # Stylesheet
│   ├── images/          # Image assets
│   └── favicon.ico      # Favicon
├── www/                 # Web pages
│   ├── index.html       # Main chat interface
│   └── login.html       # Login page
├── start_sampleapp.py   # Main application entry point
├── start_proxy.py       # Proxy server entry point
├── start_backend.py     # Backend server entry point
└── README.md            # This file
```

## File Details

### Entry Point Scripts

#### `start_sampleapp.py`
Main application entry point that can run as either a tracker or peer server.

**Key Features:**
- Supports two roles: `tracker` and `peer`
- Tracker manages peer pool, channels, and message routing
- Peer connects to tracker, registers itself, and handles P2P communication
- Implements channel-based messaging (general, random, project, help, announcements)
- Handles peer-to-peer direct messaging
- Supports broadcast messaging to all connected peers

**Command-line Arguments:**
- `--host`: Shared IP for both tracker and peer (e.g., `192.168.1.100`)
- `--server-ip`: Server bind IP (overrides `--host`)
- `--server-port`: Server port (auto-generated for peer if not specified, range: 9005-9999)
- `--tracker-port`: Tracker port (default: 9000)
- `--tracker-ip`: Full tracker address IP:PORT (overrides `--host` and `--tracker-port`)
- `--role`: Server role - `tracker` or `peer` (default: `peer`)

**Routes (Tracker):**
- `GET /get-all-channels`: Get list of all available channels
- `POST /join-channel`: Join a channel
- `POST /get-channel-messages`: Get messages from a channel
- `POST /send-channel-message`: Send message to a channel
- `POST /register-peer-pool`: Register a peer in the pool
- `POST /submit-info`: Submit peer information (username, IP, port)
- `GET /get-list`: Get list of active peers
- `POST /login`: Handle user login and peer assignment

**Routes (Peer):**
- `GET /get-all-channels`: Get all channels from tracker
- `GET /get-joined-channels`: Get channels this peer has joined
- `POST /join-channel`: Join a channel via tracker
- `POST /get-channel-messages`: Get channel messages from tracker
- `POST /send-channel-message`: Send message to channel via tracker
- `POST /submit-username`: Submit username to tracker
- `GET /get-list`: Get list of active peers (excluding self)
- `POST /connect-peer`: Connect to another peer
- `GET /get-connected-peers`: Get list of connected peers
- `POST /send-peer`: Send direct message to a peer
- `POST /receive-message`: Receive message from another peer
- `GET /get-received-messages`: Get received peer messages
- `POST /broadcast-peer`: Broadcast message to all connected peers

#### `start_proxy.py`
HTTP reverse proxy server that routes requests to backend servers based on hostname.

**Key Features:**
- Parses virtual host configuration from `config/proxy.conf`
- Supports multiple backend servers with load balancing
- Implements round-robin distribution policy
- Supports IP placeholder replacement (`$HOST` or `{{HOST}}`)

**Command-line Arguments:**
- `--host`: Shared IP for proxy server and backend replacements
- `--server-ip`: IP address to bind (overrides `--host`, default: `127.0.0.1`)
- `--server-port`: Port number to bind (default: 8080)
- `--config`: Path to proxy configuration file (default: `config/proxy.conf`)

**Configuration Format (`config/proxy.conf`):**
```
host "$HOST:8080" {
    proxy_pass http://$HOST:9000;
    proxy_pass http://$HOST:9001;
    dist_policy round-robin
}

host "tracker.local" {
    proxy_pass http://$HOST:9000;
}
```

#### `start_backend.py`
Simple backend server entry point (legacy/alternative to `start_sampleapp.py`).

**Command-line Arguments:**
- `--server-ip`: IP address to bind (default: `0.0.0.0`)
- `--server-port`: Port number to bind (default: 9000)

### Core Framework (`daemon/`)

#### `daemon/__init__.py`
Package initialization file that exports main components:
- `create_backend`: Backend server factory
- `create_proxy`: Proxy server factory
- `WeApRous`: Web framework class
- `Response`, `Request`: HTTP objects
- `HttpAdapter`: HTTP adapter
- `CaseInsensitiveDict`: Dictionary utilities
- Database functions: `register_user`, `check_user_exists`, `login_user`

#### `daemon/weaprous.py`
Core web framework class providing decorator-based routing.

**Key Features:**
- Decorator-based route registration (`@app.route()`)
- Supports multiple HTTP methods per route
- Maps routes to handler functions
- Integrates with backend server

**Usage:**
```python
app = WeApRous()
@app.route('/login', methods=['POST'])
def login(headers, body):
    return {'message': 'Logged in'}

app.prepare_address(ip, port)
app.run()
```

#### `daemon/backend.py`
Backend server implementation using sockets and threading.

**Key Features:**
- Multi-threaded server handling concurrent connections
- Socket-based TCP server
- Integrates with `HttpAdapter` for request processing
- Supports route-based request dispatching

**Functions:**
- `create_backend(ip, port, routes)`: Entry point for creating backend server
- `run_backend(ip, port, routes)`: Starts the server and listens for connections
- `handle_client(ip, port, conn, addr, routes)`: Handles individual client connections

#### `daemon/proxy.py`
Proxy server implementation with routing and load balancing.

**Key Features:**
- Virtual host-based routing
- Round-robin load balancing
- Backend health checking
- Request forwarding to backend servers

**Functions:**
- `create_proxy(ip, port, routes)`: Entry point for creating proxy server
- `run_proxy(ip, port, routes)`: Starts the proxy server
- `handle_client(ip, port, conn, addr, routes)`: Handles client requests
- `resolve_routing_policy(hostname, routes)`: Resolves backend based on routing policy
- `forward_request(host, port, request)`: Forwards request to backend
- `is_backend_alive(host, port, timeout)`: Checks if backend is available

#### `daemon/httpadapter.py`
HTTP adapter that processes requests and builds responses.

**Key Features:**
- Parses incoming HTTP requests
- Dispatches to route handlers
- Manages cookies and authentication
- Builds HTTP responses

**Key Methods:**
- `handle_client(conn, addr, routes)`: Main request handler
- `extract_cookies(req, resp)`: Extracts cookies from request
- `add_headers(request)`: Adds custom headers
- `add_response_headers(response, set_cookie)`: Adds response headers

#### `daemon/request.py`
HTTP request parsing and management.

**Key Features:**
- Parses HTTP request line (method, path, version)
- Extracts headers
- Parses cookies
- Handles request body
- Maps routes to handler functions

**Key Methods:**
- `prepare(request, routes)`: Main parsing method
- `extract_request_line(request)`: Extracts method, path, version
- `prepare_headers(request)`: Parses headers
- `prepare_cookies(cookies)`: Parses cookie header
- `prepare_body(data, files, json)`: Prepares request body

#### `daemon/response.py`
HTTP response building and content serving.

**Key Features:**
- Builds HTTP response headers
- Serves static files (HTML, CSS, images)
- MIME type detection
- JSON response building
- Error response handling (404, 401, 500)
- Redirect responses (302)

**Key Methods:**
- `build_response(request, hook_result)`: Main response builder
- `build_content(path, base_dir)`: Loads file content
- `get_mime_type(path)`: Determines MIME type
- `prepare_content_type(mime_type)`: Sets content type and base directory
- `build_json_response(data)`: Builds JSON response
- `build_redirect(location, has_cookie)`: Builds redirect response
- `build_unauthorized()`: Builds 401 response
- `build_notfound()`: Builds 404 response

#### `daemon/database.py`
User authentication database using CSV file.

**Key Features:**
- User registration
- User existence checking
- Login authentication

**Functions:**
- `register_user(username, password)`: Registers a new user
- `check_user_exists(username)`: Checks if user exists
- `login_user(username, password)`: Authenticates user

**Database File:** `db/database.csv` (CSV format: `username,password`)

#### `daemon/dictionary.py`
Case-insensitive dictionary implementation for HTTP headers.

### Web Interface (`www/`)

#### `www/index.html`
Main chat application interface.

**Features:**
- P2P direct messaging
- Channel-based group chat
- Peer connection management
- Real-time message polling
- Broadcast messaging
- User registration
- Channel joining/leaving

**UI Components:**
- **Sidebar:**
  - Connected Peers list
  - Joined Channels list
  - Notifications panel
- **Main Content:**
  - User List (all peers)
  - Channel List (all channels)
  - Peer Registration form
  - Chat window

#### `www/login.html`
User login page with username/password authentication.

### Configuration Files

#### `config/proxy.conf`
Proxy server virtual host configuration.

**Syntax:**
```
host "hostname" {
    proxy_pass http://backend:port;
    proxy_pass http://backend2:port;
    dist_policy round-robin
}
```

**Placeholders:**
- `$HOST` or `{{HOST}}`: Replaced with `--host` or `--server-ip` value

### Database Files

#### `db/database.csv`
User credentials database in CSV format.

**Format:**
```csv
username,password
user1,password1
user2,password2
```

## How to Run the Application

### Prerequisites
- Python 3.x
- No external dependencies required (uses only Python standard library)

### Running the Tracker Server

The tracker server manages peer registration and channel coordination.

```bash
# Basic usage (default port 9000)
python start_sampleapp.py --role tracker

# Custom IP and port
python start_sampleapp.py --role tracker --server-ip 192.168.1.100 --server-port 9000

# Using --host for shared IP
python start_sampleapp.py --role tracker --host 192.168.1.100 --tracker-port 9000
```

### Running a Peer Server

Peer servers connect to the tracker and can communicate with other peers.

```bash
# Basic usage (auto-generated port, connects to localhost:9000)
python start_sampleapp.py --role peer

# Connect to specific tracker
python start_sampleapp.py --role peer --tracker-ip 192.168.1.100:9000

# Custom peer port
python start_sampleapp.py --role peer --server-port 9001 --tracker-ip 192.168.1.100:9000

# Using --host for shared IP
python start_sampleapp.py --role peer --host 192.168.1.100 --tracker-port 9000
```

### Running the Proxy Server

The proxy server routes HTTP requests to backend servers.

```bash
# Basic usage (default port 8080)
python start_proxy.py

# Custom IP and port
python start_proxy.py --server-ip 192.168.1.100 --server-port 8080

# Using --host for IP replacement in config
python start_proxy.py --host 192.168.1.100 --server-port 8080

# Custom config file
python start_proxy.py --config config/custom_proxy.conf
```

### Complete Setup Example

**Terminal 1 - Start Tracker:**
```bash
python start_sampleapp.py --role tracker --host 127.0.0.1 --server-port 9000
```

**Terminal 2 - Start Peer 1:**
```bash
python start_sampleapp.py --role peer --host 127.0.0.1 --tracker-ip 127.0.0.1:9000 --server-port 9001
```

**Terminal 3 - Start Peer 2:**
```bash
python start_sampleapp.py --role peer --host 127.0.0.1 --tracker-ip 127.0.0.1:9000 --server-port 9002
```

**Terminal 4 - Start Proxy:**
```bash
python start_proxy.py --host 127.0.0.1 --server-port 8080
```

**Access the Application:**
- Open browser to `http://127.0.0.1:8080` (via proxy)
- Or directly to peer: `http://127.0.0.1:9001` or `http://127.0.0.1:9002`

### Using Hostnames (with Proxy)

To use hostnames, add entries to `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
127.0.0.1 tracker.local
127.0.0.1 peer1.local
127.0.0.1 peer2.local
```

Then access:
- `http://tracker.local:8080` - Tracker server
- `http://peer1.local:8080` - Peer 1
- `http://peer2.local:8080` - Peer 2

## Command-Line Reference

### `start_sampleapp.py`

```
usage: Backend [-h] [--host HOST] [--server-ip SERVER_IP] 
               [--server-port SERVER_PORT] [--tracker-port TRACKER_PORT]
               [--tracker-ip TRACKER_IP] [--role {tracker,peer}]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Shared IP for both tracker and peer
  --server-ip SERVER_IP
                        Server bind IP (overrides --host)
  --server-port SERVER_PORT
                        Server port (auto-generated for peer if not specified)
  --tracker-port TRACKER_PORT
                        Tracker port (default: 9000)
  --tracker-ip TRACKER_IP
                        Full tracker address IP:PORT
  --role {tracker,peer}
                        Server role (default: peer)
```

### `start_proxy.py`

```
usage: Proxy [-h] [--host HOST] [--server-ip SERVER_IP] 
             [--server-port SERVER_PORT] [--config CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Shared IP for proxy server and backend replacements
  --server-ip SERVER_IP
                        IP address to bind (overrides --host)
  --server-port SERVER_PORT
                        Port number to bind (default: 8080)
  --config CONFIG       Path to proxy configuration file
```

### `start_backend.py`

```
usage: Backend [-h] [--server-ip SERVER_IP] [--server-port SERVER_PORT]

optional arguments:
  -h, --help            show this help message and exit
  --server-ip SERVER_IP
                        IP address to bind (default: 0.0.0.0)
  --server-port SERVER_PORT
                        Port number to bind (default: 9000)
```

## Application Workflow

1. **Start Tracker**: The tracker server starts and listens for peer registrations
2. **Start Peers**: Peer servers start, register with tracker, and get assigned from peer pool
3. **User Login**: Users authenticate via login page (`/login`)
4. **Peer Assignment**: After login, user is assigned to an available peer server
5. **Registration**: User registers username with their assigned peer
6. **Connect**: User can connect to other peers from the user list
7. **Chat**: Users can send direct messages, join channels, or broadcast messages

## Features

- **P2P Direct Messaging**: Send messages directly to other peers
- **Channel Chat**: Join channels and participate in group conversations
- **Broadcast Messaging**: Send messages to all connected peers
- **User Management**: Register usernames and view active peers
- **Real-time Updates**: Polling-based message retrieval
- **Load Balancing**: Proxy supports round-robin distribution
- **Authentication**: Cookie-based session management

## Notes

- The application uses polling (every 3 seconds) for message retrieval
- Peer ports are auto-generated in range 9005-9999 if not specified
- Tracker manages channel messages and peer memberships
- Direct peer-to-peer connections are established via socket connections
- All communication uses HTTP/1.1 protocol

## License

Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
All rights reserved.
This file is part of the CO3093/CO3094 course,
and is released under the "MIT License Agreement".

