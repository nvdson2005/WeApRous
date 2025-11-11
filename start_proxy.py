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
start_proxy
~~~~~~~~~~~

Entry point for launching a proxy server using Python's socket framework.

This module parses command-line arguments to configure the server's IP
address and port, reads virtual host definitions from a configuration
file, and initializes the proxy server with routing information.
"""

import socket
import threading
import argparse
import re
from urllib.parse import urlparse
from collections import defaultdict

from daemon import create_proxy

PROXY_PORT = 8080


def parse_virtual_hosts(config_file, host_ip=None):
    """
    Parse virtual host blocks from a config file.

    Args:
        config_file (str): Path to the configuration file.
        host_ip (str): Optional IP to replace placeholders in config.

    Returns:
        dict: Dictionary mapping hostnames to tuples of (backends, policy).
              Each backend can be a string or list of backend URLs.
    """
    with open(config_file, 'r') as f:
        config_text = f.read()

    # Replace placeholders with actual IP if provided
    if host_ip:
        # Replace $HOST or {{HOST}} with actual IP
        config_text = config_text.replace('$HOST', host_ip)
        config_text = config_text.replace('{{HOST}}', host_ip)

    # Match each host block
    pattern = r'host\s+"([^"]+)"\s*\{(.*?)\}'
    host_blocks = re.findall(pattern, config_text, re.DOTALL)

    dist_policy_map = ""

    routes = {}
    for host, block in host_blocks:
        proxy_map = {}

        # Find all proxy_pass entries
        proxy_passes = re.findall(
            r'proxy_pass\s+http://([^\s;]+);',
            block
        )
        proxy_list = proxy_map.get(host, [])
        proxy_list = proxy_list + proxy_passes
        proxy_map[host] = proxy_list

        # Find dist_policy if present
        policy_match = re.search(r'dist_policy\s+(-\w+)', block)
        if policy_match:
            dist_policy_map = policy_match.group(1)
        else:
            # Default policy is round_robin
            dist_policy_map = 'round-robin'

        # Build the mapping and policy
        if len(proxy_map.get(host, [])) == 1:
            routes[host] = (proxy_map.get(host, [])[0], dist_policy_map)
        else:
            routes[host] = (proxy_map.get(host, []), dist_policy_map)

    for key, value in routes.items():
        print(key, value)
    return routes


def main():
    """
    Entry point for launching the proxy server.

    Parses command-line arguments to determine the server's IP address
    and port, then calls create_proxy to start the proxy server.

    Command-line Arguments:
        --host (str): Shared IP for proxy and backends (e.g., 192.168.1.100)
        --server-ip (str): IP address to bind (overrides --host, default: 0.0.0.0)
        --server-port (int): Port number to bind (default: 8080)
        --config (str): Path to proxy config file (default: config/proxy.conf)
    """
    parser = argparse.ArgumentParser(
        prog='Proxy',
        description='Start the proxy server process',
        epilog='Proxy daemon'
    )
    parser.add_argument(
        '--host',
        default=None,
        help='Shared IP for proxy server and backend replacements'
    )
    parser.add_argument(
        '--server-ip',
        default=None,
        help='IP address to bind the server (overrides --host)'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=PROXY_PORT,
        help=f'Port number to bind the server. Default is {PROXY_PORT}.'
    )
    parser.add_argument(
        '--config',
        default='config/proxy.conf',
        help='Path to proxy configuration file'
    )

    args = parser.parse_args()
    
    # Determine server IP: priority is --server-ip > --host > '0.0.0.0'
    if args.server_ip:
        ip = args.server_ip
    elif args.host:
        ip = args.host
    else:
        ip = '127.0.0.1'
    
    # Use --host for config replacement (or server_ip if host not specified)
    replace_ip = args.host or args.server_ip
    
    port = args.server_port

    print(f"[Proxy] Starting on {ip}:{port}")
    print(f"[Proxy] Loading config from {args.config}")
    if replace_ip:
        print(f"[Proxy] Replacing placeholders with IP: {replace_ip}")

    routes = parse_virtual_hosts(args.config, replace_ip)

    create_proxy(ip, port, routes)


if __name__ == "__main__":
    main()