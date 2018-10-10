CREATE TABLE Gene(
    locus CHAR(10),
    length INTEGER CHECK (length >= 0),
    start INTEGER CHECK (start >= 0),
    stop INTEGER CHECK (stop >= start),
    name TEXT,
    chromosome INTEGER,
    sequence TEXT,

    PRIMARY KEY(locus)
);

CREATE TABLE Annotations(
    locus CHAR(10),
    accession VARCHAR(10),
    name TEXT,
    description TEXT,
    start INTEGER,
    stop INTEGER,
    length INTEGER,
    score DOUBLE,
    expected DOUBLE,

    FOREIGN KEY(locus) REFERENCES Gene(locus)
);

CREATE TABLE Protein(
    locus CHAR(10),
    product TEXT,
    transcript TEXT,

    FOREIGN KEY(locus) REFERENCES Gene(locus)
);
