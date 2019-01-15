# coding: utf-8

import typing

import Bio.Alphabet.IUPAC
import Bio.Seq
import Bio.SeqRecord


class Gene(typing.NamedTuple):
    locus: str
    length: int
    start: int
    stop: int
    strand: bool
    name: str
    chromosome: int
    sequence: int

    def to_seq_record(self):
        seq = Bio.Seq.Seq(self.sequence, alphabet=Bio.Alphabet.IUPAC.ambiguous_dna)
        return Bio.SeqRecord.SeqRecord(seq, self.locus, description=self.name)


class Annotation(typing.NamedTuple):
    locus: str
    accession: str
    name: str
    description: str
    length: int
    start: int
    stop: int
    score: float
    evalue: float


class Transcript(typing.NamedTuple):
    locus: str
    product: str
    transcript: str
