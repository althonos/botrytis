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
        return Gene(*row) if row is not None else None

    def transcript(self, locus):
        cursor = sqlite3.connect(self.db).cursor()
        cursor.execute("SELECT * FROM transcript WHERE locus=?", (locus,))
        row = cursor.fetchone()
        return Transcript(*row) if row is not None else None
