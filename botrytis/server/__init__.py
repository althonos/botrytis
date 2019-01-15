# coding: utf-8

import io

import Bio.Seq
import Bio.SeqRecord
import Bio.SeqIO
import cherrypy
import jinja2

from ..db import BotrytisDB
from . import filters


class BotrytisHandler(object):

    def __init__(self, db, env):
        self.db = db
        self.env = env
        self._cp_config = {'error_page.404': self.error404}

    def error404(self, traceback, message, status, version):
        template = self.env.get_template('error.html')
        return template.render(message=message, status=status)


@cherrypy.popargs("locus")
class Gene(BotrytisHandler):

    @cherrypy.expose
    def index(self, locus=None):
        gene = locus if locus is None else self.db.gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)
        template = self.env.get_template('gene.html')
        return template.render(gene=gene)


@cherrypy.popargs("locus")
class Download(BotrytisHandler):

    @cherrypy.expose
    def gb(self, locus=None):
        gene = locus if locus is None else self.db.gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)

        cherrypy.response.headers['Content-Type'] = 'chemical/x-genbank'
        cherrypy.response.headers['Content-Disposition'] = f'attachment; filename={locus}.gb'

        res = io.StringIO()
        record = gene.to_seq_record()
        Bio.SeqIO.write(record, res, "gb")
        return res.getvalue().encode()




class BotrytisWebsite(BotrytisHandler):

    def __init__(self):

        # --- Variables ---
        super().__init__(
            BotrytisDB(),
            jinja2.Environment(
                loader=jinja2.PackageLoader('botrytis', 'pages'),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
        )

        # --- Custom jinja2 filters ---
        self.env.filters['sentence'] = filters.sentence

        # --- Subfolder handlers ---
        self.gene = Gene(self.db, self.env)
        self.download = Download(self.db, self.env)

    @cherrypy.expose
    def index(self):
        return """<html>Hello, world!</html>"""
