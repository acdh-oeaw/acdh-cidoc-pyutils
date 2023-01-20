[![flake8 Lint](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/lint.yml/badge.svg)](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/lint.yml)
[![Test](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/test.yml/badge.svg)](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/acdh-oeaw/acdh-cidoc-pyutils/branch/main/graph/badge.svg?token=XRF7ANN1TM)](https://codecov.io/gh/acdh-oeaw/acdh-cidoc-pyutils)
[![PyPI version](https://badge.fury.io/py/acdh-cidoc-pyutils.svg)](https://badge.fury.io/py/acdh-cidoc-pyutils)

# acdh-cidoc-pyutils
Helper functions for the generation of CIDOC CRMish RDF

## Usage

* install via `pip install acdh-cidoc-pyutils`

### date-like-string to casted rdflib.Literal

```python
from acdh_cidoc_pyutils import date_to_literal
dates = [
    "1900",
    "1900-01",
    "1901-01-01",
    "foo",
]
for x in dates:
    date_literal = date_to_literal(x)
    print((date_literal.datatype))

# returns
# http://www.w3.org/2001/XMLSchema#gYear
# http://www.w3.org/2001/XMLSchema#gYearMonth
# http://www.w3.org/2001/XMLSchema#date
# http://www.w3.org/2001/XMLSchema#string
```

### make some random URI

```python
from acdh_cidoc_pyutils import make_uri

domain = "https://hansi4ever.com/"
version = "1"
prefix = "sumsi"
uri = make_uri(domain=domain, version=version, prefix=prefix)
print(uri)
# https://hansi4ever.com/1/sumsi/6ead32b8-9713-11ed-8065-65787314013c

uri = make_uri(domain=domain)
print(uri)
# https://hansi4ever.com/8b912e66-9713-11ed-8065-65787314013c
```

### create an E52_Time-Span graph

```python
from acdh_cidoc_pyutils import create_e52, make_uri
uri = make_uri()
e52 = create_e52(uri, begin_of_begin="1800-12-12", end_of_end="1900-01")
print(e52.serialize())

# returns
# @prefix ns1: <http://www.cidoc-crm.org/cidoc-crm/> .
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# <https://hansi4ever.com/387fb457-971b-11ed-8065-65787314013c> a ns1:E52_Time-Span ;
#     rdfs:label "1800-12-12 - 1900-01"^^xsd:string ;
#     ns1:P82a_begin_of_the_begin "1800-12-12"^^xsd:date ;
#     ns1:P82b_end_of_the_end "1900-01"^^xsd:gYearMonth .
```

### normalize_string

```python
from acdh_cidoc_pyutils import normalize_string
string = """\n\nhallo
mein schatz ich liebe    dich
    du bist         die einzige für mich
        """
print(normalize_string(string))
# returns
# hallo mein schatz ich liebe dich du bist die einzige für mich
```

### extract date attributes (begin, end)

expects typical TEI date attributes like `@when, @when-iso, @notBefore, @notAfter` and returns a tuple containg start- and enddate values. If only `@when or @when-iso` or only `@notBefore or @notAfter` are provided, the returned values are the same

```python
from lxml.etree import Element
from acdh_cidoc_pyutils import extract_begin_end

date_string = "1900-12-12"
date_object = Element("{http://www.tei-c.org/ns/1.0}tei")
date_object.attrib["when-iso"] = date_string
print(extract_begin_end(date_object))

# returns
# ('1900-12-12', '1900-12-12')

date_object = Element("{http://www.tei-c.org/ns/1.0}tei")
date_object.attrib["notAfter"] = "1900-12-12"
date_object.attrib["notBefore"] = "1800"
print(extract_begin_end(date_object))

# returns
# ('1800', '1900-12-12')
```


## development

* `pip install -r requirements_dev.txt`
* `flake8` -> linting
* `coveage run -m pytest` -> runs tests and creates coverage stats