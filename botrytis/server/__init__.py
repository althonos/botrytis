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
        self._cp_config = {
            'error_page.404': self._cp_error,
            'error_page.403': self._cp_error,
            'error_page.500': self._cp_error,
        }

    def _cp_error(self, traceback, message, status, version):
        template = self.env.get_template('error.html')
        return template.render(message=message, status=status, traceback=traceback)


@cherrypy.popargs("locus")
class Gene(BotrytisHandler):

    def gene(self, locus):
        """Serve a page for a given gene.
        """
        gene = self.db.gene(locus)
        if gene is None:
            msg = f"No locus provided" if locus is None else f"No gene with locus {locus!r}"
            raise cherrypy.HTTPError(404, msg)
        template = self.env.get_template('gene/page.html')
        return template.render(gene=gene)

    @cherrypy.expose
    def index(self, locus=None):
        """Serve a gene index.
        """
        if locus is not None:
            return self.gene(locus)
        template = self.env.get_template('gene/index.html')
        return template.render()







@cherrypy.popargs("accession")
class Annotation(BotrytisHandler):

    def annotation(self, accession):
        annotations = self.db.annotations(accession)
        if annotations is None:
            msg = f"No annotation with accession {accession!r}"
            raise cherrypy.HTTPError(404, msg)
        template = self.env.get_template("annotation/page.html")
        return template.render(annotations=annotations)

    @cherrypy.expose
    def index(self, accession=None):
        if accession is not None:
            return self.annotation(accession)
        template = self.env.get_template("annotation/index.html")
        return template.render()



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
        self.annotation = Annotation(self.db, self.env)
        self.gene = Gene(self.db, self.env)
        self.download = Download(self.db, self.env)

    @cherrypy.expose
    def index(self):
        return """<html>Hello, world!</html>"""
