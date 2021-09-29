"""
Serve packages (Development ONLY)
"""

# Copyright 2021 Croix Bleue du Québec

# This file is part of python-noops.

# python-noops is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# python-noops is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with python-noops.  If not, see <https://www.gnu.org/licenses/>.

import functools
import os
import logging
from http.server import socketserver, SimpleHTTPRequestHandler

def serve_forever(directory: str, bind: str, port: int):
    """Start a web server"""
    server_address = (
        bind or "0.0.0.0",
        port or 8080
    )

    if directory is None:
        directory = os.getcwd()

    handler = functools.partial(SimpleHTTPRequestHandler, directory=directory)

    logging.warning("Serve is not recommended for production.")
    with socketserver.TCPServer(server_address, handler) as httpd:
        print(f"Connect on http://{server_address[0]}:{server_address[1]}.")
        httpd.serve_forever()
