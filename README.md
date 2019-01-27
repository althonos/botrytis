# The Botrytis Viewer

*A minimal webapp to display Botrytis cinerea sequencing data using CherryPy, Jinja2 and Bootstrap*

[![Source](https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=86400&style=flat-square&logo=github)](https://github.com/althonos/botrytis)
[![Docker](https://img.shields.io/badge/docker%20build-automatic-blue.svg?maxAge=86400&style=flat-square&logo=docker)](https://hub.docker.com/r/althonos/botrytis/)

## Usage

Clone the repository and download frontend requirements using:
```console
$ python setup.py build_js
```

Then serve the website with:
```console
$ python setup.py run
```

## Dependencies

[BLAST+](https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=Download)
binaries are required to run blasts against the *Botrytis cinerea* genome.

The Botrytis Viewer is built with CherryPy and Jinja2 (backend) and Bootstrap (frontend).


## About

This pipeline was developed by [Martin Larralde](https://github.com/althonos) for the
*web programming* course of the [AMI2B Master's degree](http://www.bibs.u-psud.fr/m2_ami2b.php)
of [Université Paris-Sud](https://www.u-psud.fr).
