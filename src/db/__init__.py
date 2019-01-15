# coding: utf-8

import sqlite3

from .model import Gene, Annotation, Transcript
from .generate import generate_db


# class Db(object):
#
#     def __init__(
#         self,
#         path=pkg_resources.resource_filename(__name__, "botrytis.db"),
#     ):
#         pass
