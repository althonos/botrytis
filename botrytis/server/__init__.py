# coding: utf-8

import jinja2
import cherrypy

from ..db import BotrytisDB


@cherrypy.popargs("locus")
class Gene(object):

    def __init__(self, db, env):
        self.db = db
        self.env = env
        self._cp_config = {'error_page.404': self.error404}

    @cherrypy.expose
    def index(self, locus=None):
        gene = locus if locus is None else self.db.gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)
        template = self.env.get_template('gene.html')
        return template.render(gene=gene)

    def error404(self, *args, **kwargs):
        print(args, kwargs)
        template = self.env.get_template('404.html')
        return template.render()



class BotrytisWebsite(object):

    def __init__(self):

        # --- Variables ---
        self.db = db = BotrytisDB()
        self.env = env = jinja2.Environment(
            loader=jinja2.PackageLoader('botrytis', 'pages'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

        # --- Subfolder handlers ---
        self.gene = Gene(db, env)


    def error404(self):
        return "<html>fuck me, a 404 Error!</html>"


    @cherrypy.expose
    def index(self):
        return """<html>Hello, world!</html>"""
