# coding: utf-8

import typing

import Bio.Alphabet.IUPAC
import Bio.Seq
import Bio.SeqRecord
import Bio.SeqFeature


class Gene(typing.NamedTuple):
    locus: str
    length: int
    start: int
    stop: int
    strand: bool
    name: str
    chromosome: int
    sequence: int
    annotations: typing.Optional[typing.List['Annotation']]

    def to_seq_record(self):
        seq = Bio.Seq.Seq(self.sequence, alphabet=Bio.Alphabet.IUPAC.ambiguous_dna)
        record = Bio.SeqRecord.SeqRecord(seq, self.locus, description=self.name)
        record.annotations['topology'] = 'linear'
        record.features = [a.to_seq_feature() for a in self.annotations or ()]
        return record


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
    gene: typing.Optional['Gene']

    def to_seq_feature(self):
        return Bio.SeqFeature.SeqFeature(
            type="misc_feature",
            strand=1,
            qualifiers={
                'label': self.accession,
                'note': [self.name, self.description],
                'db_xref': f"PFAM:{self.accession}",
            },
            location=Bio.SeqFeature.FeatureLocation(
                start=self.start - self.gene.start,
                end=self.stop - self.gene.start,
            )
        )


class Transcript(typing.NamedTuple):
    locus: str
    product: str
    transcript: str
