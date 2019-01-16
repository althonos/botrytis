# coding: utf-8
"""botrytis - serve the Botrytis Genome Viewer.

Usage:
    botrytis [-p PORT] [-s STATIC]

Arguments:
    -p PORT, --port PORT        The port the server should listen to
                                [default: 8080].

"""

import os

import docopt
import cherrypy

from . import __name__
from .server import BotrytisWebsite


args = docopt.docopt(__doc__)
cwd = os.path.abspath(os.getcwd())

cherrypy.quickstart(
    BotrytisWebsite(),
    "/",
    {
        "/static": {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": os.path.join(cwd, "ext")
        },
        "/static/img": {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": os.path.join(cwd, "static", "img")
        }
    }
)
