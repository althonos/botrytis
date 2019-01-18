# coding: utf-8

import os
import pkg_resources
import shutil
import tempfile

import Bio.SeqRecord
import Bio.Blast.NCBIXML
from Bio.Blast import Applications as Apps

_DB_PATH =  os.path.relpath(
    pkg_resources.resource_filename(__name__, "runtime/botrytis"),
    os.getcwd(),
)

def _blast(query, application, db=_DB_PATH, **options):
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as fa:
            Bio.SeqIO.write(query, fa, 'fasta')
        app = application(
            query=fa.name,
            db=db,
            out=f"{fa.name}.xml",
            outfmt=5,
            **options
        )
        out, err = app()
        with open(f"{fa.name}.xml") as xml:
            return Bio.Blast.NCBIXML.read(xml)
    finally:
        shutil.rmtree(fa.name, ignore_errors=True)
        shutil.rmtree(f"{fa.name}.xml", ignore_errors=True)

def blastn(query, db=_DB_PATH, task='blastn'):
    return _blast(query, Apps.NcbiblastnCommandline, db, task=task)

def blastp(query, db=_DB_PATH, task='blastp'):
    return _blast(query, Apps.NcbiblastpCommandline, db, task=task)

def blastx(query, db=_DB_PATH, task='blastx'):
    return _blast(query, Apps.NcbiblastxCommandline, db, task=task)
