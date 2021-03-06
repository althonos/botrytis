-- Gene ------------------------------------------------------------------------
CREATE TABLE Gene(
    locus      CHAR(10),
    length     INTEGER CHECK (length >= 0),
    start      INTEGER CHECK (start >= 0),
    stop       INTEGER CHECK (stop >= start),
    -- strand (true for direct, false otherwise)
    strand     BOOLEAN,
    name       TEXT,
    contig     INTEGER,
    -- gene sequence
    sequence   TEXT,

    PRIMARY KEY (locus)
);

-- Domain ----------------------------------------------------------------------
CREATE TABLE Domain(
    accession VARCHAR(10),
    name TEXT,
    description TEXT,

    PRIMARY KEY (accession)
);

-- Annotation ------------------------------------------------------------------
CREATE TABLE Annotation(
    -- annotated gene
    locus CHAR(10),
    -- annotation accession
    accession VARCHAR(10),
    -- location
    length INTEGER CHECK (length >= 0),
    start INTEGER CHECK (start >= 0),
    stop INTEGER CHECK (stop >= start),
    -- score
    score DOUBLE,
    evalue DOUBLE,

    FOREIGN KEY (locus) REFERENCES Gene(locus)
    FOREIGN KEY (accession) REFERENCES Annotation(accession)
);

CREATE INDEX Annotation_Locus ON Annotation(locus);
CREATE INDEX Annotation_Accession ON Annotation(accession);

-- Transcripts -----------------------------------------------------------------
CREATE TABLE Transcript(
    locus CHAR(10),
    -- protein sequence
    product TEXT,
    -- transcript sequence
    transcript TEXT,

    FOREIGN KEY(locus) REFERENCES Gene(locus)
);
