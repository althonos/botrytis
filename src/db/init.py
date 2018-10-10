#!/bin/env python

import contextlib
import collections
import itertools
import os
import sqlite3
import tqdm

import Bio.SeqIO

STATIC_DIR = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'static'))

Gene = collections.namedtuple("Gene", [
    "locus",
    "length",
    "start",
    "stop",
    "name",
    "chromosome",
    "sequence"
])


if __name__ == "__main__":

    # Load genes records
    records_g = {
        r.id: r
        for r in Bio.SeqIO.parse(
            os.path.join(STATIC_DIR, "genes.fasta"),
            "fasta"
        )
    }

    # Load genes from the genome summary
    genes = []
    with open(os.path.join(STATIC_DIR, "genome_summary_per_gene.txt")) as f:
        for line in itertools.islice(f, 1, None):
            locus, _, _, length, start, stop, strand, name, chromosome, *_ = line.split('\t')
            seq = str(records_g[locus].seq)
            genes.append(Gene(locus, int(length), int(start), int(stop), name, int(chromosome), seq))

    # Load annotations from

    # Remove the old database
    if os.path.exists("botrytis.db"):
        os.remove("botrytis.db")

    # Connect with SQLite3
    with contextlib.closing(sqlite3.connect("botrytis.db")) as sql:

        # Create tables
        with open("createTables.sql") as f:
            statements = f.read().split(';')
            for statement in statements:
                sql.execute(statement)

        # Populate Genes
        for gene in tqdm.tqdm(genes, desc="genes"):
            sql.execute("INSERT INTO Gene VALUES (?, ?, ?, ?, ?, ?, ?);", (
                gene.locus,
                gene.length,
                gene.start,
                gene.stop,
                gene.name,
                gene.chromosome,
                gene.sequence
            ))
        sql.execute("COMMIT")

        # Populate
