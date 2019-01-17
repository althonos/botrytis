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
    contig: int
    sequence: int
    annotations: typing.Optional[typing.List['Annotation']]

    def with_annotations(self, annotations):
        return type(self)(*self[:-1], annotations=annotations)

    def to_seq_record(self):
        seq = Bio.Seq.Seq(self.sequence, alphabet=Bio.Alphabet.IUPAC.ambiguous_dna)
        record = Bio.SeqRecord.SeqRecord(seq, self.locus, description=self.name)
        record.annotations['topology'] = 'linear'
        record.features = [a.to_seq_feature() for a in self.annotations or ()]
        return record


class Domain(typing.NamedTuple):
    accession: str
    name: str
    description: str
    annotations: typing.Optional[typing.List['Annotation']]

    def with_annotations(self, annotations):
        return type(self)(*self[:-1], annotations=annotations)

class Annotation(typing.NamedTuple):
    gene: Gene
    domain: Domain
    length: int
    start: int
    stop: int
    score: float
    evalue: float

    def to_seq_feature(self):
        return Bio.SeqFeature.SeqFeature(
            type="misc_feature",
            strand=1,
            qualifiers={
                'label': self.domain.accession,
                'note': [self.domain.name, self.domain.description],
                'db_xref': f"PFAM:{self.domain.accession}",
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
