#!/bin/env python

import contextlib
import collections
import itertools
import os
import pkg_resources
import sqlite3
import sys

import Bio.SeqIO

from .model import Annotation, Gene, Transcript


_DEFAULT_OUTPUT = os.path.relpath(
    pkg_resources.resource_filename(__name__, "botrytis.db"),
    os.getcwd(),
)

_DATA_DIRECTORY = os.path.relpath(
    pkg_resources.resource_filename(__name__, "data"),
    os.getcwd(),
)


def generate_sql_db(data_dir=_DATA_DIRECTORY, output=_DEFAULT_OUTPUT):

    def load_indexed(filename):
        return {
            r.id: r
            for r in Bio.SeqIO.parse(os.path.join(data_dir, filename), "fasta")
        }

    # Load genes records, proteins, transcripts
    records_g = load_indexed("genes.fasta")
    records_p = load_indexed("proteins.fasta")
    records_t = load_indexed("transcripts.fasta")

    # Build a mapping of protein to transcript
    prot_to_transcript = dict(
        map(str.strip, r.description.split('|', 2)[:2])
        for r in records_p.values()
    )

    # Load genes from the genome summary
    genes = []
    with open(os.path.join(data_dir, "genome_summary_per_gene.txt")) as f:
        for line in itertools.islice(f, 1, None):
            locus, _, _, length, start, stop, strand, name, contig, *_ = line.split('\t')
            seq = str(records_g[locus].seq)
            genes.append(Gene(locus, int(length), int(start), int(stop), strand, name, int(contig), seq, None))

    # Load annotations from the PFAM to genes mapping
    index = set()
    pfam = []
    with open(os.path.join(data_dir, "pfam_to_genes.txt")) as f:
        for line in itertools.islice(f, 1, None):
            _, locus, contig, accession, name, description, start, stop, length, score, evalue = line.strip().split('\t')
            # remove duplicate annotations (indentical annotations in the same place with different scores)
            if (accession, start, stop) not in index:
                index.add((accession, start, stop))
                pfam.append(Annotation(locus, accession, name, description, int(length), int(start), int(stop), float(score), float(evalue), None))

    # Remove the old database
    if os.path.exists(output):
        os.remove(output)

    # Connect with SQLite3
    with contextlib.closing(sqlite3.connect(output)) as sql:

        # Create tables
        with pkg_resources.resource_stream(__name__, "generate.sql") as f:
            statements = f.read().decode().split(';')
            for statement in statements:
                sql.execute(statement)

        # Populate Genes
        for gene in genes:
            sql.execute("INSERT INTO Gene VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (
                gene.locus,
                gene.length,
                gene.start,
                gene.stop,
                True if gene.strand == '+' else False,
                gene.name,
                gene.contig,
                gene.sequence
            ))
        sql.execute("COMMIT")

        # Populate PFAM
        for annot in pfam:
            sql.execute("INSERT INTO Annotation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", (
                annot.locus,
                annot.accession,
                annot.name,
                annot.description,
                annot.length,
                annot.start,
                annot.stop,
                annot.score,
                annot.evalue
            ))
        sql.execute("COMMIT")

        # Populate transcript
        for prot in records_p.values():
            transcript, locus = prot.description.split(' | ', 2)[:2]
            sql.execute("INSERT INTO Transcript VALUES (?, ?, ?);", (
                locus,
                str(records_p[transcript].seq),
                str(records_t[transcript].seq),
            ))
        sql.execute("COMMIT")


if __name__ == "__main__":
    try:
        generate_sql_db()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
