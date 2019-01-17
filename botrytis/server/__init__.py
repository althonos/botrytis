# coding: utf-8

import io
import math
import random

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
            'error_page.400': self._cp_error,
            'error_page.404': self._cp_error,
            'error_page.403': self._cp_error,
            'error_page.500': self._cp_error,
        }

    def _cp_error(self, traceback, message, status, version):
        template = self.env.get_template('error.html')
        return template.render(message=message, status=status, traceback=traceback)


@cherrypy.popargs("locus")
class Gene(BotrytisHandler):

    PAGESIZE = 10

    SORT_KEYS = {
        "locus": "Locus",
        "start": "Start location",
        "stop": "End location",
        "length": "Length"
    }

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
    def index(self, locus=None, sort="locus", page=1):
        """Serve a gene index.
        """
        if locus is not None:
            return self.gene(locus)
        if sort not in self.SORT_KEYS:
            raise cherrypy.HTTPError(400, f"invalid parameter: sort={sort!r}")
        try:
            page = int(page)
        except ValueError:
            raise cherrypy.HTTPError(400, f"invalid parameter: page={sort!r}")
        genes, total = self.db.genes(
            sort=sort, page=page, pagesize=self.PAGESIZE)
        template = self.env.get_template('gene/index.html')
        return template.render(
            genes=genes,
            page=page,
            sort=sort,
            total=math.ceil(total/self.PAGESIZE),
            sort_keys=self.SORT_KEYS
        )


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
    def index(self, accession=None, page=1):
        if accession is not None:
            return self.annotation(accession)
        template = self.env.get_template("annotation/index.html")
        return template.render(page=page)


@cherrypy.popargs("locus")
class Download(BotrytisHandler):

    @cherrypy.expose
    def gb(self, locus=None):
        gene = None if locus is None else self.db.gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)
        return self._download(gene, 'gb', 'chemical/x-genbank', 'gb')

    @cherrypy.expose
    def fasta(self, locus=None):
        gene = None if locus is None else self.db.gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)
        return self._download(gene, 'fasta', 'application/x-fasta', 'fa')

    def _download(self, gene, format, mimetype, extension):
        cherrypy.response.headers.update({
            'Content-Type': f'{mimetype}',
            'Content-Disposition': f'attachment; filename={gene.locus}.{extension}'
        })
        res = io.StringIO()
        record = gene.to_seq_record()
        Bio.SeqIO.write(record, res, format)
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
        template = self.env.get_template("splash/index.html")
        return template.render(background=random.randint(1, 3))
