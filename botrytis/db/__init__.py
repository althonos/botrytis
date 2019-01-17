# coding: utf-8

import functools
import sqlite3
import pkg_resources

from .model import Annotation, Domain, Gene, Transcript


class BotrytisDB(object):

    def __init__(self, path=pkg_resources.resource_filename(__name__, "botrytis.db")):
        self.db = path

    @functools.lru_cache(maxsize=3)
    def _columns(self, table):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in iter(cursor.fetchone, None)]

    def gene(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute(
            """
            SELECT *
            FROM gene
            WHERE locus=?
            """,
            (locus,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        gene = Gene(*row, annotations=[])
        cursor.execute(
            """
            SELECT
                 a.length, a.start, a.stop, a.score, a.evalue,
                d.accession, d.name, d.description
            FROM Annotation a, Domain d
            WHERE a.locus=?
              AND a.accession=d.accession
            """,
            (locus,)
        )
        for row in iter(cursor.fetchone, None):
            domain = Domain(*row[5:], annotations=[])
            annot = Annotation(gene, domain, *row[:5])
            domain.annotations.append(annot)
            gene.annotations.append(annot)
        return gene

    def genes(self, sort="locus", page=1, pagesize=10, ascending=True):
        cursor = sqlite3.connect(self.db).cursor()
        if not isinstance(page, int) or not isinstance(pagesize, int):
            raise TypeError("page and pagesize must be integers")
        if sort not in self._columns('Gene'):
            raise ValueError(f"unexpected sort key: {sort!r}")
        cursor.execute(
            f"""
            SELECT locus
            FROM Gene
            ORDER BY {sort} {"ASC" if ascending else "DESC"}
            LIMIT {pagesize} OFFSET {(page-1)*pagesize}
            """,
        )
        genes = [self.gene(*row) for row in iter(cursor.fetchone, None)]
        total, *_ = cursor.execute("SELECT COUNT(*) FROM Gene").fetchone()
        return (genes, total)

    def domain(self, accession):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute(
            """
            SELECT *
            FROM Domain
            WHERE accession=?
            """,
            (accession,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        domain = Domain(*row, annotations=[])
        cursor.execute(
            """
            SELECT
                 a.length, a.start, a.stop, a.score, a.evalue,
                 g.locus, g.length, g.start, g.stop, g.strand, g.name, g.contig, g.sequence
            FROM Annotation a, Gene g
            WHERE a.accession=?
              AND a.locus=g.locus
            """,
            (accession,)
        )
        for row in iter(cursor.fetchone, None):
            annot = Annotation(Gene(*row[5:], annotations=None), domain, *row[:5])
            domain.annotations.append(annot)
        return domain

    def transcript(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM transcript WHERE locus=?", (locus,))
        row = cursor.fetchone()
        return Transcript(*row) if row is not None else None
