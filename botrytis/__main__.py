# coding: utf-8
f"""botrytis - serve the Botrytis Genome Viewer.

Usage:
    botrytis [-p PORT] [-s STATIC]

Arguments:
    -p PORT, --port PORT        The port the server should listen to
                                [default: 8080].
    -s STATIC, --static STATIC  The location to the `static` folder
                                [default: ./static]

"""

import docopt
import cherrypy

from .server import BotrytisWebsite


args = docopt.docopt(__doc__)


cherrypy.quickstart(BotrytisWebsite())
