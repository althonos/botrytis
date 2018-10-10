#!/bin/env python

import contextlib
import collections
import itertools
import os
import sqlite3

import Bio.SeqIO
import tqdm

STATIC_DIR = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'static'))

Gene = collections.namedtuple("Gene", [
    "locus",
    "length",
    "start",
    "stop",
    "strand",
    "name",
    "chromosome",
    "sequence"
])

Annotation = collections.namedtuple("Annotation", [
    "locus",
    "accession",
    "name",
    "description",
    "length",
    "start",
    "stop",
    "score",
    "expected",
])


def load_indexed(filename):
    return {
        r.id: r
        for r in Bio.SeqIO.parse(
            os.path.join(STATIC_DIR, filename),
            "fasta"
        )
    }



if __name__ == "__main__":

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
    with open(os.path.join(STATIC_DIR, "genome_summary_per_gene.txt")) as f:
        for line in itertools.islice(f, 1, None):
            locus, _, _, length, start, stop, strand, name, chromosome, *_ = line.split('\t')
            seq = str(records_g[locus].seq)
            genes.append(Gene(locus, int(length), int(start), int(stop), strand, name, int(chromosome), seq))

    # Load annotations from the PFAM to genes mapping
    pfam = []
    with open(os.path.join(STATIC_DIR, "pfam_to_genes.txt")) as f:
        for line in itertools.islice(f, 1, None):
            _, locus, contig, accession, name, description, start, stop, length, score, expected = line.strip().split('\t')
            pfam.append(Annotation(locus, accession, name, description, int(length), int(start), int(stop), float(score), float(expected)))

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
            sql.execute("INSERT INTO Gene VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (
                gene.locus,
                gene.length,
                gene.start,
                gene.stop,
                True if gene.strand == '+' else False,
                gene.name,
                gene.chromosome,
                gene.sequence
            ))
        sql.execute("COMMIT")

        # Populate PFAM
        for annot in tqdm.tqdm(pfam, desc="pfam "):
            sql.execute("INSERT INTO Annotation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", (
                annot.locus,
                annot.accession,
                annot.name,
                annot.description,
                annot.length,
                annot.start,
                annot.stop,
                annot.score,
                annot.expected
            ))
        sql.execute("COMMIT")

        # Populate transcript
        for prot in tqdm.tqdm(records_p.values(), desc="prots"):
            transcript, locus = prot.description.split(' | ', 2)[:2]
            sql.execute("INSERT INTO Transcript VALUES (?, ?, ?);", (
                locus,
                str(records_p[transcript].seq),
                str(records_t[transcript].seq),
            ))
        sql.execute("COMMIT")
