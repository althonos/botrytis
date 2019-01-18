# coding: utf-8

import functools
import sqlite3
import pkg_resources

from .model import Annotation, Domain, Gene, Transcript


class BotrytisDB(object):

    def __init__(
        self,
        path=pkg_resources.resource_filename(__name__, "runtime/botrytis.sqlite3")
    ):
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
        gene = Gene(*row, annotations=None)
        return gene

    def _annotation_from_gene(self, cursor, gene):
        cursor.execute(
            f"""
            SELECT a.length, a.start, a.stop, a.score, a.evalue,
                   d.accession, d.name, d.description
              FROM Annotation a, Domain d
             WHERE a.accession=d.accession
               AND a.locus=?
            """,
            (gene.locus,)
        )
        return [
            Annotation(gene, Domain(*row[5:], annotations=None), *row[:5])
            for row in iter(cursor.fetchone, None)
        ]

    def _annotation_from_domain(self, cursor, domain):
        cursor.execute(
            f"""
            SELECT a.length, a.start, a.stop, a.score, a.evalue,
                   g.locus, g.length, g.start, g.stop, g.strand, g.name, g.contig, g.sequence
              FROM Annotation a, Gene g
             WHERE a.locus=g.locus
               AND a.accession=?
            """,
            (domain.accession,)
        )
        return [
            Annotation(Gene(*row[5:], annotations=None), domain, *row[:5])
            for row in iter(cursor.fetchone, None)
        ]

    def annotations(self, *, gene=None, domain=None):
        cursor = sqlite3.connect(self.db).cursor()
        if gene is None and domain is None:
            raise ValueError("give either a gene or a domain")
        elif gene is not None and domain is not None:
            raise ValueError("give either a gene or a domain, not both")
        elif domain is None:
            return self._annotation_from_gene(cursor, gene)
        else:
            return self._annotation_from_domain(cursor, domain)

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
        domain = Domain(*row, annotations=None)
        return domain

    def domains(self, sort="accession", page=1, pagesize=10, ascending=True):
        cursor = sqlite3.connect(self.db).cursor()
        if not isinstance(page, int) or not isinstance(pagesize, int):
            raise TypeError("page and pagesize must be integers")
        if sort not in self._columns('Domain') and sort != "count":
            raise ValueError(f"unexpected sort key: {sort!r}")

        if sort == "count":
            cursor.execute(
                f"""
                  SELECT a.accession
                    FROM Domain d, Annotation a
                   WHERE a.accession=d.accession
                GROUP BY a.accession
                ORDER BY count(*) {"ASC" if ascending else "DESC"}
                   LIMIT {pagesize} OFFSET {(page-1)*pagesize}
                """
            )
        else:
            cursor.execute(
                f"""
                  SELECT accession
                    FROM Domain
                ORDER BY {sort} {"ASC" if ascending else "DESC"}
                   LIMIT {pagesize} OFFSET {(page-1)*pagesize}
                """
            )

        domains = [self.domain(*row) for row in iter(cursor.fetchone, None)]
        total, *_ = cursor.execute("SELECT COUNT(*) FROM Gene").fetchone()
        return (domains, total)

    def transcript(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM transcript WHERE locus=?", (locus,))
        row = cursor.fetchone()
        return Transcript(*row) if row is not None else None
