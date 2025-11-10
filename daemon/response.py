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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
import json
from .dictionary import CaseInsensitiveDict

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
    print(f"{ANSI_BLUE}{ANSI_BOLD}[DEBUG] {msg} {args}{ANSI_RESET}")

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            mime_type = None
        
        if mime_type is None:
            if path.endswith('.html') or path == "/" or path == "/index.html" or path == "/login":
                mime_type = 'text/html'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """
        
        base_dir = ""

        # Processing mime_type based on main_type and sub_type
        main_type, sub_type = mime_type.split('/', 1)
        log_info("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            elif sub_type == 'csv':
                base_dir = BASE_DIR+"csv/"
            elif sub_type == 'xml':
                base_dir = BASE_DIR+"xml/"
            else:
                # handle_text_other(sub_type)
                raise ValueError("Invalid text type: sub_type={}".format(sub_type))
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application':
            base_dir = BASE_DIR+"apps/"
            self.headers['Content-Type']='application/{}'.format(sub_type)
        elif main_type == 'video':
            base_dir = BASE_DIR+"videos/"
            self.headers['Content-Type']='video/{}'.format(sub_type)
        #
        #  TODO: process other mime_type
        #        application/xml       
        #        application/zip
        #        ...
        #        text/csv
        #        text/xml
        #        ...
        #        video/mp4 
        #        video/mpeg
        #        ...
        #
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        log_info("[Response] serving the object at location {}".format(filepath))
            #
            #  TODO: implement the step of fetch the object file
            #        store in the return value of content
            #
        with open(filepath, 'rb') as f:
            content = f.read()
        return len(content), content


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Max-Forward": "10",
                "Pragma": "no-cache",
                "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
            }

        for k, v in rsphdr.items():
            headers[k] = v

        fmt_header = "HTTP/1.1 200 OK\r\n"
        for k, v in headers.items():
            fmt_header += "{}: {}\r\n".format(k, v)
        fmt_header += "\r\n"
        return str(fmt_header).encode('utf-8')


    def build_notfound_with_json(self, body):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """
        body = body.encode('utf-8')
        header = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: {}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).format(len(body))

        return (header.encode('utf-8') + body)

    def build_unauthorized(self):
        """
        Constructs a standard 401 Unauthorized HTTP response.

        :rtype bytes: Encoded 401 response.
        """

        return (
                "HTTP/1.1 401 Unauthorized\r\n"
                # "WWW-Authenticate: Basic realm=\"Access to the site\"\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 16\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "401 Unauthorized"
            ).encode('utf-8')

    def build_redirect(self, location, has_cookie = False):
        """
        Constructs a standard 302 Redirect HTTP response.

        :params location (str): URL to redirect to.
        :params has_cookie (bool): Whether to include a Set-Cookie header.

        :rtype bytes: Encoded 302 response.
        """

        header = (
                "HTTP/1.1 302 Found\r\n"
                "Location: {}\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
            ).format(location)

        if has_cookie:
            header += "Set-Cookie: auth=true\r\n"

        header += "Connection: close\r\n\r\n"

        body = "302 Found"

        return (header + body).encode('utf-8')
    
    def build_internal_server_error(self):
        """
        Constructs a standard 500 Internal Server Error HTTP response.

        :rtype bytes: Encoded 500 response.
        """

        return (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 25\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "500 Internal Server Error"
            ).encode('utf-8')
    
    def build_json_response(self, data):
        """
        Constructs a JSON HTTP response.

        :params data (str): JSON string to include in the response body.

        :rtype bytes: Encoded JSON response.
        """

        body = data.encode('utf-8')
        header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: {}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).format(len(body))

        return (header.encode('utf-8') + body)
    
    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 13\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')

    # def build_response(self, request, hook_result=None):
    #     """
    #     Builds a full HTTP response including headers and content based on the request.

    #     :params request (class:`Request <Request>`): incoming request object.

    #     :rtype bytes: complete HTTP response using prepared headers and content.
    #     """

    #     path = request.path
    #     log_info("[Response] building response for path {}".format(path))
    #     mime_type = self.get_mime_type(path)
    #     log_info("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

    #     base_dir = ""
    #     if path == "/get-channel-messages":
    #         if request.method == "GET":
    #             if hook_result is not None:
    #                 return self.build_json_response(json.dumps(hook_result))
    #             else:
    #                 return self.build_internal_server_error()
    #     if path == "/send-channel-message":
    #         if request.method == "POST":
    #             if hook_result is not None:
    #                 return self.build_json_response(json.dumps(hook_result))
    #             else:
    #                 return self.build_internal_server_error()
    #     if path == "/get-joined-channels":
    #         if request.method == "GET":
    #             if hook_result is not None:
    #                 return self.build_json_response('{ "status": "success", "channels": %s }' % json.dumps(hook_result))
    #             else:
    #                 return self.build_internal_server_error()
    #     if path == "/get-all-channels":
    #         if request.method == "GET":
    #             if hook_result is not None:
    #                 return self.build_json_response('{"status": "success", "channels": %s}' % json.dumps(hook_result)) 
    #             else:
    #                 return self.build_internal_server_error()
    #     if path == "/join-channel":
    #         print("[Response] join-channel hook_result: {}".format(hook_result))
    #         if hook_result is not None:
    #             return self.build_json_response(json.dumps(hook_result))
    #     if path == "/submit-username": 
    #         if hook_result is not None:
    #             if hook_result == True:
    #                 return self.build_json_response('{"status": "success"}')
    #             elif hook_result == False:
    #                 return self.build_json_response('{"status": "failure"}')
    #         else:
    #             return self.build_internal_server_error()
    #     if path == "/broadcast-peer" and request.method == "POST":
    #         if hook_result is not None:
    #             if 'status' in hook_result:
    #                 if hook_result['status'] == 'success':
    #                     return self.build_json_response('{"status": "success", "message": "Broadcast sent"}')
    #                 else:
    #                     return self.build_internal_server_error()
    #         else:
    #             return self.build_internal_server_error()
    #     if path == "/get-received-messages" or path == "/get-connected-peers":
    #         if request.method == "GET":
    #             return self.build_json_response(hook_result)
    #     if path == "/login":
    #         if request.method == "GET":
    #             base_dir = self.prepare_content_type(mime_type = 'text/html')
    #             path = "login.html"
    #             mime_type = 'text/html'
    #         elif request.method == "POST":
    #             if hook_result is not None:
    #                 if 'set_cookie' in hook_result:
    #                     if hook_result['set_cookie'] == 'auth=true':
    #                         if 'chosen_peer' in hook_result and hook_result['chosen_peer'] is not None:
    #                             return self.build_redirect(location=hook_result['redirect'], has_cookie=True)
    #                         else:
    #                             return self.build_internal_server_error()
    #                     else:
    #                         return self.build_unauthorized()
    #             else:
    #                 return self.build_internal_server_error()
    #     if path == "/register-peer-pool":
    #         if hook_result is not None:
    #             if hook_result == True:
    #                 return self.build_json_response('{"status": "success"}')
    #             elif hook_result == False:
    #                 return self.build_internal_server_error()
    #         else:
    #             return self.build_internal_server_error()
    #     if path == "/get-list":
    #         if request.method == "GET":
    #             return self.build_json_response(hook_result)
    #     if path == "/submit-info":
    #         if hook_result is not None:
    #             if hook_result == True:
    #                 return self.build_json_response('{"status": "success"}')
    #             elif hook_result == False:
    #                 return self.build_json_response('{"status": "failure"}')
    #         else:
    #             return self.build_internal_server_error()
    #     if path == "/connect-peer":
    #         if hook_result is not None:
    #             if 'status' in hook_result:
    #                 if hook_result['status'] == 'success':
    #                     return self.build_json_response('{"status": "success", "message": "%s"}' % hook_result['message'])
    #                 else:
    #                     return self.build_json_response('{"status": "error", "message": "%s"}' % hook_result['message'])
    #         else:
    #             return self.build_internal_server_error()
    #     if path == "/send-peer":
    #         if hook_result is not None:
    #             if 'status' in hook_result:
    #                 if hook_result['status'] == 'success':
    #                     return self.build_json_response('{"status": "success", "message": "%s"}' % hook_result['message'])
    #                 else:
    #                     # return self.build_notfound_with_json('{"status": "error", "message": "%s"}' % hook_result['message'])
    #                     return self.build_json_response('{"status": "error", "message": "%s"}' % hook_result['message'])
    #         else:
    #             return self.build_internal_server_error()
    #     if path == "/receive-message":
    #         if hook_result is not None:
    #             if 'status' in hook_result:
    #                 if hook_result['status'] == 'success':
    #                     return self.build_json_response('{"status": "success", "message": "%s"}' % hook_result['message'])
    #                 else:
    #                     return self.build_json_response('{"status": "error", "message": "%s"}' % hook_result['message'])
    #     if hook_result is not None:
    #         if 'set_cookie' in hook_result:
    #             if hook_result['set_cookie'] == 'auth=true':
    #                 return self.build_redirect(location=hook_result['redirect'], has_cookie=True)
    #                 # self.headers['Set-Cookie'] = hook_result['set_cookie']
    #                 # path = hook_result['content_path']
    #                 # mime_type = self.get_mime_type(path)
    #                 # base_dir = self.prepare_content_type(mime_type = mime_type)
    #             else:
    #                 return self.build_unauthorized()
    #     else:
    #         #If HTML, parse and serve embedded objects
    #         if (path == "/login" or path == "login.html") and request.method == "GET":
    #             base_dir = self.prepare_content_type(mime_type = 'text/html')
    #             path = "login.html"
    #             mime_type = 'text/html'
    #         elif path == "/" or path == "/index.html":
    #             if request.cookies != 'auth=true':
    #                 return self.build_unauthorized()
    #             base_dir = self.prepare_content_type(mime_type = 'text/html')
    #             path = "index.html"
    #             mime_type = 'text/html'
    #         elif path.endswith('favicon.ico'):
    #             mime_type = 'image/x-icon'
    #             base_dir = self.prepare_content_type(mime_type = 'image/x-icon')
    #             self.headers['Content-Type']='image/x-icon'
    #         elif path.endswith('.html') or mime_type == 'text/html':
    #             base_dir = self.prepare_content_type(mime_type = 'text/html')
    #         elif mime_type == 'text/css':
    #             base_dir = self.prepare_content_type(mime_type = 'text/css')
    #         elif mime_type == 'image/png' or mime_type == 'image/jpeg' or mime_type == 'image/gif' or mime_type == 'image/x-icon':
    #             base_dir = self.prepare_content_type(mime_type='image/png')
    #         else:
    #             return self.build_notfound()

    #     c_len, self._content = self.build_content(path, base_dir)
    #     self._header = self.build_response_header(request)

    #     return self._header + self._content
    def build_response(self, request, hook_result=None):
        path = request.path
        method = request.method
        log_info("[Response] building response for path {}".format(path))
        mime_type = self.get_mime_type(path)
        log_info("[Response] {} path {} mime_type {}".format(method, path, mime_type))

        # --- API Endpoints ---
        # Each API endpoint is handled with an early return
        api_routes = {
            ("/get-channel-messages", "POST"): lambda: self.build_json_response(json.dumps(hook_result)) if hook_result else self.build_internal_server_error(),
            ("/send-channel-message", "POST"): lambda: self.build_json_response(json.dumps(hook_result)) if hook_result else self.build_internal_server_error(),
            ("/get-joined-channels", "GET"): lambda: self.build_json_response('{ "status": "success", "channels": %s }' % json.dumps(hook_result)) if hook_result != None else self.build_internal_server_error(),
            ("/get-all-channels", "GET"): lambda: self.build_json_response('{"status": "success", "channels": %s}' % json.dumps(hook_result)) if hook_result else self.build_internal_server_error(),
            ("/join-channel", "POST"): lambda: self.build_json_response(json.dumps(hook_result)) if hook_result else self.build_internal_server_error(),
            ("/submit-username", "POST"): lambda: self.build_json_response('{"status": "success"}') if hook_result == True else self.build_json_response('{"status": "failure"}') if hook_result == False else self.build_internal_server_error(),
            ("/broadcast-peer", "POST"): lambda: self.build_json_response('{"status": "success", "message": "Broadcast sent"}') if hook_result and hook_result.get('status') == 'success' else self.build_internal_server_error(),
            ("/get-received-messages", "GET"): lambda: self.build_json_response(hook_result),
            ("/get-connected-peers", "GET"): lambda: self.build_json_response(hook_result),
            ("/register-peer-pool", "POST"): lambda: self.build_json_response('{"status": "success"}') if hook_result == True else self.build_internal_server_error(),
            ("/get-list", "GET"): lambda: self.build_json_response(hook_result),
            ("/submit-info", "POST"): lambda: self.build_json_response('{"status": "success"}') if hook_result == True else self.build_json_response('{"status": "failure"}') if hook_result == False else self.build_internal_server_error(),
            ("/connect-peer", "POST"): lambda: self.build_json_response('{"status": "success", "message": "%s"}' % hook_result['message']) if hook_result and hook_result.get('status') == 'success' else self.build_json_response('{"status": "error", "message": "%s"}' % hook_result['message']) if hook_result else self.build_internal_server_error(),
            ("/send-peer", "POST"): lambda: self.build_json_response('{"status": "success", "message": "%s"}' % hook_result['message']) if hook_result and hook_result.get('status') == 'success' else self.build_json_response('{"status": "error", "message": "%s"}' % hook_result['message']) if hook_result else self.build_internal_server_error(),
            ("/receive-message", "POST"): lambda: self.build_json_response('{"status": "success", "message": "%s"}' % hook_result['message']) if hook_result and hook_result.get('status') == 'success' else self.build_json_response('{"status": "error", "message": "%s"}' % hook_result['message']) if hook_result else self.build_internal_server_error(),
        }

        api_key = (path, method)
        if api_key in api_routes:
            return api_routes[api_key]()

        # --- Special Handling for /login ---
        if path == "/login":
            if method == "GET":
                base_dir = self.prepare_content_type(mime_type='text/html')
                path = "login.html"
                mime_type = 'text/html'
            elif method == "POST":
                if hook_result is not None and 'set_cookie' in hook_result:
                    if hook_result['set_cookie'] == 'auth=true':
                        if 'chosen_peer' in hook_result and hook_result['chosen_peer'] is not None:
                            return self.build_redirect(location=hook_result['redirect'], has_cookie=True)
                        else:
                            return self.build_internal_server_error()
                    else:
                        return self.build_unauthorized()
                else:
                    return self.build_internal_server_error()

        # --- Cookie-based Redirects ---
        if hook_result is not None and 'set_cookie' in hook_result:
            if hook_result['set_cookie'] == 'auth=true':
                return self.build_redirect(location=hook_result['redirect'], has_cookie=True)
            else:
                return self.build_unauthorized()

        # --- Static File Serving ---
        # If HTML, parse and serve embedded objects
        if (path == "/login" or path == "login.html") and method == "GET":
            base_dir = self.prepare_content_type(mime_type='text/html')
            path = "login.html"
            mime_type = 'text/html'
        elif path == "/" or path == "/index.html":
            if request.cookies != 'auth=true':
                return self.build_unauthorized()
            base_dir = self.prepare_content_type(mime_type='text/html')
            path = "index.html"
            mime_type = 'text/html'
        elif path.endswith('favicon.ico'):
            mime_type = 'image/x-icon'
            base_dir = self.prepare_content_type(mime_type='image/x-icon')
            self.headers['Content-Type'] = 'image/x-icon'
        elif path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type='text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type='text/css')
        elif mime_type in ['image/png', 'image/jpeg', 'image/gif', 'image/x-icon']:
            base_dir = self.prepare_content_type(mime_type='image/png')
        else:
            return self.build_notfound()

        c_len, self._content = self.build_content(path, base_dir)
        self._header = self.build_response_header(request)
        return self._header + self._content