CREATE TABLE Gene(
    locus      CHAR(10),
    length     INTEGER CHECK (length >= 0),
    start      INTEGER CHECK (start >= 0),
    stop       INTEGER CHECK (stop >= start),
    -- strand (true for direct, false otherwise)
    strand     BOOLEAN,
    name       TEXT,
    chromosome INTEGER,
    -- gene sequence
    sequence   TEXT,

    PRIMARY KEY(locus)
);

CREATE TABLE Annotation(
    locus CHAR(10),
    accession VARCHAR(10),
    name TEXT,
    description TEXT,
    length INTEGER CHECK (length >= 0),
    start INTEGER CHECK (start >= 0),
    stop INTEGER CHECK (stop >= start),
    score DOUBLE,
    expected DOUBLE,

    FOREIGN KEY (locus) REFERENCES Gene(locus)
);

CREATE INDEX Annotation_Locus ON Annotation(locus);
CREATE INDEX Annotation_Accession ON Annotation(accession);

CREATE TABLE Transcript(
    locus CHAR(10),

    -- protein sequence
    product TEXT,
    -- transcript sequence
    transcript TEXT,

    FOREIGN KEY(locus) REFERENCES Gene(locus)
);
