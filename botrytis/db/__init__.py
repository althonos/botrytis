# coding: utf-8

import sqlite3
import pkg_resources

from .model import Gene, Annotation, Transcript


class BotrytisDB(object):

    def __init__(self, path=pkg_resources.resource_filename(__name__, "botrytis.db")):
        self.db = path

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
            SELECT *
            FROM Annotation
            WHERE locus=?
            """,
            (locus,)
        )
        for row in cursor.fetchall():
            gene.annotations.append(Annotation(*row, gene=gene))
        return gene

    def genes(self, sort="locus", page=1, pagesize=10, ascending=True):
        cursor = sqlite3.connect(self.db).cursor()
        if not isinstance(page, int) or not isinstance(pagesize, int):
            raise TypeError("page and pagesize must be integers")
        keys = {row[1] for row in cursor.execute("PRAGMA table_info('Gene')").fetchall()}
        if sort not in keys:
            raise ValueError(f"unexpected sort key: {sort!r}")
        cursor.execute(
            f"""
            SELECT locus
            FROM Gene
            ORDER BY {sort} {"ASC" if ascending else "DESC"}
            LIMIT {pagesize} OFFSET {(page-1)*pagesize}
            """,
        )
        genes = [self.gene(*row) for row in cursor.fetchall()]
        total, *_ = cursor.execute("SELECT COUNT(*) FROM Gene").fetchone()
        return (genes, total)

    def annotations(self, accession):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute(
            """
            SELECT *
            FROM Annotation
            WHERE accession=?
            ORDER BY locus
            """,
            (accession,)
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return [Annotation(*row, gene=self.gene(row[0])) for row in rows]

    def transcript(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM transcript WHERE locus=?", (locus,))
        row = cursor.fetchone()
        return Transcript(*row) if row is not None else None
