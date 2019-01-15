# coding: utf-8

import jinja2
import cherrypy


DEFAULT_CONFIGURATION = {
    "/": {
        "tools.session.on": True,
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './public'
    }
}


class BotrytisWebsite(object):

    def __init__(self):
        l = jinja2.PackageLoader('botrytis', 'pages')
        print("TEMPLATES:", l.list_templates())
        self.env = jinja2.Environment(
            loader=jinja2.PackageLoader('botrytis', 'pages'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    @cherrypy.expose
    def index(self):
        return """<html>Hello, world!</html>"""

    @cherrypy.expose
    def gene(self, id=None):
        template = self.env.get_template('gene.html')
        return template.render()

        # if id is None:
        #     return """<html>Not found.</html>"""
        # return f"""<html>Requested gene: {id}</html>"""
