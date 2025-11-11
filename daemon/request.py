#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
import base64
class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        # print("[DEBUG] Raw request:" + repr(request))
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()
            # print("[Request] Extracted request line METHOD {} PATH {} VERSION {}".format(method, path, version))

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))
        
        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))

        self.headers = self.prepare_headers(request)
        cookies = self.headers.get('cookie', '')
        if cookies != '':
            self.cookies = cookies
            self.prepare_cookies(cookies)
            # print("cookies:", self.cookies['auth'])
        body_pattern = '\r\n\r\n'
        body = request.split(body_pattern, 1)[1] if body_pattern in request else ''
        self.prepare_body(body, files=None, json=None)
        return

    def prepare_body(self, data, files, json=None):
        self.prepare_content_length(data)
        # The parsing body data will be handled in the hook function
        self.body = data 
        return


    def prepare_content_length(self, body):
        # Ensure headers dict exists
        if self.headers is None:
            self.headers = {}
        
        # Compute byte length correctly for str/bytes/None
        if body is None:
            length = 0
        elif isinstance(body, (bytes, bytearray)):
            length = len(body)
        else:
            # treat as str-like and encode to compute byte length
            length = len(str(body).encode('utf-8'))
        
        # Use lower-case key to match prepare_headers' keys
        self.headers["content-length"] = str(length)
        return


    def prepare_auth(self, auth, url=""):
        header = auth or self.headers.get("authorization", "")
        if not header:
            return
        header = header.strip()
        low = header.lower()
        #Basic authentication
        if low.startswith("basic "):
            b64 = header.split(None, 1)[1]
            try:
                decoded = base64.b64decode(b64).decode("utf-8")
                username, password = decoded.split(":", 1)
                self.auth = (username, password)
            except Exception:
                self.auth = ("basic", None)
        # Bearer authentication
        elif low.startswith("bearer "):
            token = header.split(None, 1)[1]
            self.auth = ("bearer", token)
        # Digest authentication
        elif low.startswith("digest "):
            self.auth = ("digest", header)
        else:
            self.auth = ("unknown", None)
        return

    def prepare_cookies(self, cookies):
        # Ensure headers dict exists
        if self.headers is None:
            self.headers = {}

        # If cookies is a header string like "a=1; b=2", parse it into a dict
        if isinstance(cookies, str):
            parsed = CaseInsensitiveDict()
            for part in cookies.split(';'):
                part = part.strip()
                if not part:
                    continue
                if '=' in part:
                    name, val = part.split('=', 1)
                    parsed[name.strip()] = val.strip()
                else:
                    parsed[part] = ""
            self.cookies = parsed
        # If cookies is already a dict-like object, copy into CaseInsensitiveDict
        elif isinstance(cookies, dict):
            self.cookies = CaseInsensitiveDict({k: (v if v is not None else "") for k, v in cookies.items()})
        else:
            # unknown type: store string representation
            self.cookies = CaseInsensitiveDict()
            if cookies is not None:
                self.cookies["__raw__"] = str(cookies)

        # Build canonical Cookie header (name=value; name2=value2)
        cookie_pairs = [f"{k}={v}" for k, v in self.cookies.items()]
        if cookie_pairs:
            self.headers["cookie"] = "; ".join(cookie_pairs)
        else:
            # remove cookie header if no cookies
            self.headers.pop("cookie", None)
        return
