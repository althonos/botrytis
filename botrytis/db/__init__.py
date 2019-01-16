# coding: utf-8

import sqlite3
import pkg_resources

from .model import Gene, Annotation, Transcript
from .generate import generate_db


class BotrytisDB(object):

    def __init__(self, path=pkg_resources.resource_filename(__name__, "botrytis.db")):
        self.db = path

    def gene(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM gene WHERE locus=?", (locus,))
        row = cursor.fetchone()
        if row is None:
            return None
        gene = Gene(*row, annotations=[])
        cursor.execute("SELECT * FROM annotation WHERE locus=?", (locus,))
        for row in cursor.fetchall():
            gene.annotations.append(Annotation(*row, gene=gene))
        return gene

    def annotations(self, accession):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM annotation WHERE accession=? ORDER BY locus", (accession,))
        rows = cursor.fetchall()
        if not rows:
            return None
        return [Annotation(*row, gene=self.gene(row[0])) for row in rows]

    def transcript(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM transcript WHERE locus=?", (locus,))
        row = cursor.fetchone()
        return Transcript(*row) if row is not None else None
