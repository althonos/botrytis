# coding: utf-8

import io
import math
import random
import re
import shutil
import tempfile
import threading

import Bio.Alphabet
import Bio.Seq
import Bio.SeqRecord
import Bio.SeqIO
import cherrypy
import jinja2
from Bio.Blast import Applications as BlastApp

from ..db import BotrytisDB
from ..db.blast import blastn, blastp, blastx
from ..db.generate import generate_sql_db
from . import filters


class BotrytisHandler(object):

    PAGESIZE = 11
    SORT_KEYS = {}

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
        template = self.env.get_template('error.html.j2')
        return template.render(message=message, status=status, traceback=traceback)

    def _validate_parameters(self, sort=None, page=None, order=None):
        if sort is not None and sort not in self.SORT_KEYS:
            raise cherrypy.HTTPError(400, f"invalid parameter: sort={sort!r}")
        if page is not None:
            try:
                page = int(page)
            except ValueError:
                raise cherrypy.HTTPError(400, f"invalid parameter: page={sort!r}")
        if order is not None and order not in {"asc", "desc"}:
            raise cherrypy.HTTPError(400, f"invalid parameter: order={order!r}")


@cherrypy.popargs("locus")
class Gene(BotrytisHandler):

    SORT_KEYS = {
        "locus": "Locus",
        "start": "Start location",
        "stop": "End location",
        "length": "Length",
        "contig": "Contig",
    }

    def gene(self, locus):
        """Serve a page for a given gene.
        """
        gene = self.db.gene(locus)
        if gene is None:
            msg = f"No locus provided" if locus is None else f"No gene with locus {locus!r}"
            raise cherrypy.HTTPError(404, msg)
        if gene.annotations is None:
            gene = gene.with_annotations(self.db.annotations(gene=gene))
        template = self.env.get_template('gene/page.html.j2')
        return template.render(gene=gene)

    @cherrypy.expose
    def index(self, locus=None, sort="locus", page=1, order="asc"):
        """Serve a gene index.
        """
        if locus is not None:
            return self.gene(locus)
        self._validate_parameters(page=page, sort=sort, order=order)
        genes, total = self.db.genes(
            sort=sort,
            page=int(page),
            pagesize=self.PAGESIZE,
            ascending=order=="asc",
        )
        template = self.env.get_template('gene/index.html.j2')
        return template.render(
            genes=genes,
            page=int(page),
            sort=sort,
            ascending=order=="asc",
            total=math.ceil(total/self.PAGESIZE),
            sort_keys=self.SORT_KEYS
        )


@cherrypy.popargs("accession")
class Domain(BotrytisHandler):

    SORT_KEYS = {
        "accession": "Accession",
        "name": "Name",
        "count": "Occurrences",
    }

    def domain(self, accession):
        domain = self.db.domain(accession)
        if domain is None:
            msg = f"No domain with accession {accession!r}"
            raise cherrypy.HTTPError(404, msg)
        if domain.annotations is None:
            domain = domain.with_annotations(self.db.annotations(domain=domain))
        template = self.env.get_template("domain/page.html.j2")
        return template.render(domain=domain)

    @cherrypy.expose
    def index(self, accession=None, page=1, sort="accession", order="asc"):
        if accession is not None:
            return self.domain(accession)
        self._validate_parameters(page=page, sort=sort, order=order)
        domains, total = self.db.domains(
            sort=sort,
            page=int(page),
            pagesize=self.PAGESIZE,
            ascending=order=="asc",
        )
        domains = [d.with_annotations(self.db.annotations(domain=d)) for d in domains]
        template = self.env.get_template('domain/index.html.j2')
        return template.render(
            domains=domains,
            page=int(page),
            sort=sort,
            ascending=order=="asc",
            total=math.ceil(total/self.PAGESIZE),
            sort_keys=self.SORT_KEYS
        )


@cherrypy.popargs("locus")
class Download(BotrytisHandler):

    @cherrypy.expose
    def gb(self, locus=None):
        gene = None if locus is None else self._gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)
        return self._download(gene, 'gb', 'chemical/x-genbank', 'gb')

    @cherrypy.expose
    def fasta(self, locus=None):
        gene = None if locus is None else self._gene(locus)
        if gene is None:
            raise cherrypy.HTTPError(404)
        return self._download(gene, 'fasta', 'application/x-fasta', 'fa')

    def _gene(self, locus):
        gene = self.db.gene(locus)
        return gene.with_annotations(self.db.annotations(gene=gene))

    def _download(self, gene, format, mimetype, extension):
        cherrypy.response.headers.update({
            'Content-Type': f'{mimetype}',
            'Content-Disposition': f'attachment; filename={gene.locus}.{extension}'
        })
        res = io.StringIO()
        record = gene.to_seq_record()
        Bio.SeqIO.write(record, res, format)
        return res.getvalue().encode()


@cherrypy.popargs("query")
class Search(BotrytisHandler):

    @cherrypy.expose
    def index(self, query=None, page=1):

        self._validate_parameters(page=page)

        # redirect to a gene if given a gene ID
        gene = self.db.gene(query)
        if gene is not None:
            raise cherrypy.HTTPRedirect(f"/gene/{gene.locus}")

        # redirect to an annotation if given an accession
        domain = self.db.domain(query)
        if domain is not None:
            raise cherrypy.HTTPRedirect(f"/domain/{domain.accession}")

        # query the db
        if query is None:
            genes, total = [], 0
        else:
            query = query.strip()
            genes, total = self.db.search_genes(query, page=int(page))

        # default search result
        template = self.env.get_template('search.html.j2')
        return template.render(
            query=query,
            results=genes,
            total=math.ceil(total/self.PAGESIZE),
            page=int(page)
        )


class Blast(BotrytisHandler):

    _RX_TRIM = re.compile("\s")
    _RX_VALIDATE_N = re.compile(f"^[{Bio.Alphabet.IUPAC.ambiguous_dna.letters}]+$")
    _RX_VALIDATE_P = re.compile(f"^[{Bio.Alphabet.IUPAC.protein.letters}]+$")

    def _validate_sequence_n(self, seq):
        if not self._RX_VALIDATE_N.match(seq):
            raise cherrypy.HTTPError(400, "invalid nucleotide sequence")

    def _validate_sequence_p(self, seq):
        if not self._RX_VALIDATE_P.match(seq):
            raise cherrypy.HTTPError(400, "invalid protein sequence")


    @cherrypy.expose
    def result(self, sequence, type):

        sequence = self._RX_TRIM.sub("", sequence)

        if type == "blastn" or type=="blastx":
            if not self._RX_VALIDATE_N.match(sequence):
                raise cherrypy.HTTPError(400, "invalid nucleotide sequence")
            alphabet = Bio.Alphabet.IUPAC.extended_dna
        elif type=="blastp":
            if not self._RX_VALIDATE_P.match(sequence):
                raise cherrypy.HTTPError(400, "invalid protein sequence")
            alphabet = Bio.Alphabet.IUPAC.protein
        else:
            raise cherrypy.HTTPError(400, f"invalid type: {type!r}")

        seq = Bio.Seq.Seq(sequence, alphabet)
        record = Bio.SeqRecord.SeqRecord(id='query', seq=seq)
        result = {"blastn": blastn, "blastp": blastp, "blastx": blastx}[type](record)

        template = self.env.get_template("blast/result.html.j2")
        return template.render(result=result)

    @cherrypy.expose
    def p(self):
        template = self.env.get_template("blast/p.html.j2")
        return template.render()

    @cherrypy.expose
    def n(self):
        template = self.env.get_template("blast/n.html.j2")
        return template.render()

    @cherrypy.expose
    def x(self):
        template = self.env.get_template("blast/x.html.j2")
        return template.render()


class BotrytisWebsite(BotrytisHandler):

    def __init__(self):

        # --- Generate SQLite DB ---
        cherrypy.log("   DB Generating SQL database...")
        generate_sql_db()

        # --- Variables ---
        super().__init__(
            BotrytisDB(),
            jinja2.Environment(
                loader=jinja2.PackageLoader('botrytis', 'pages'),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
        )

        # --- Custom jinja2 filters ---
        for name in dir(filters):
            if not name.startswith('_'):
                self.env.filters[name] = getattr(filters, name)

        # --- Subfolder handlers ---
        self.domain = Domain(self.db, self.env)
        self.gene = Gene(self.db, self.env)
        self.download = Download(self.db, self.env)
        self.search = Search(self.db, self.env)
        self.blast = Blast(self.db, self.env)

    @cherrypy.expose
    def index(self):
        template = self.env.get_template("splash.html.j2")
        return template.render()
