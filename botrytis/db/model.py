# coding: utf-8

import typing


class Gene(typing.NamedTuple):
    locus: str
    length: int
    start: int
    stop: int
    strand: bool
    name: str
    chromosome: int
    sequence: int


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
