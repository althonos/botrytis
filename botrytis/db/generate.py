#!/bin/env python

import contextlib
import collections
import itertools
import os
import pkg_resources
import sqlite3
import sys

import Bio.SeqIO
from Bio.Blast.Applications import NcbimakeblastdbCommandline

from .model import Annotation, Domain, Gene, Transcript


_DEFAULT_OUTPUT = os.path.relpath(
    pkg_resources.resource_filename(__name__, "runtime"),
    os.getcwd(),
)

_DATA_DIRECTORY = os.path.relpath(
    pkg_resources.resource_filename(__name__, "data"),
    os.getcwd(),
)


def generate_sql_db(
    data_dir=_DATA_DIRECTORY,
    output=os.path.join(_DEFAULT_OUTPUT, 'botrytis.sqlite3')
):

    output_dir = os.path.dirname(output)
    os.makedirs(output_dir, exist_ok=True)

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
    genes = {}
    with open(os.path.join(data_dir, "genome_summary_per_gene.txt")) as f:
        for line in itertools.islice(f, 1, None):
            locus, _, _, length, start, stop, strand, name, contig, *_ = line.split('\t')
            seq = str(records_g[locus].seq)
            genes[locus] = Gene(locus, int(length), int(start), int(stop), '+' in strand, name, int(contig), seq, None)

    # Load annotations from the PFAM to genes mapping
    domains = {}
    annots = []
    index = set()
    with open(os.path.join(data_dir, "pfam_to_genes.txt")) as f:
        for line in itertools.islice(f, 1, None):
            _, locus, contig, accession, name, description, start, stop, length, score, evalue = line.strip().split('\t')
            domains[accession] = domain = Domain(accession, name, description, None)
            # remove duplicate annotations (indentical annotations in the same place with different scores)
            if (accession, start, stop) not in index:
                index.add((accession, start, stop))
                annots.append(Annotation(genes[locus], domain, int(length), int(start), int(stop), float(score), float(evalue)))

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
        for gene in genes.values():
            sql.execute("INSERT INTO Gene VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (
                gene.locus,
                gene.length,
                gene.start,
                gene.stop,
                gene.strand,
                gene.name,
                gene.contig,
                gene.sequence,
            ))
        sql.execute("COMMIT")

        # Populate Domains
        for domain in domains.values():
            sql.execute("INSERT INTO Domain VALUES (?, ?, ?)", (
                domain.accession,
                domain.name,
                domain.description,
            ))
        sql.execute("COMMIT")

        # Populate PFAM
        for annot in annots:
            sql.execute("INSERT INTO Annotation VALUES (?, ?, ?, ?, ?, ?, ?);", (
                annot.gene.locus,
                annot.domain.accession,
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


def generate_blastn_db(
    data_dir=_DATA_DIRECTORY,
    output=os.path.join(_DEFAULT_OUTPUT, 'botrytis')
):
    cline = NcbimakeblastdbCommandline(
        dbtype='nucl',
        out=output,
        title="Botrytis",
        input_file=os.path.join(_DATA_DIRECTORY, 'genes.fasta')
    )
    cline()


def generate_blastp_db(
    data_dir=_DATA_DIRECTORY,
    output=os.path.join(_DEFAULT_OUTPUT, 'botrytis')
):
    cline = NcbimakeblastdbCommandline(
        dbtype='prot',
        out=output,
        title="Botrytis",
        input_file=os.path.join(_DATA_DIRECTORY, 'proteins.fasta')
    )
    cline()


if __name__ == "__main__":
    try:
        generate_sql_db()
        generate_blastn_db()
        generate_blastp_db()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
