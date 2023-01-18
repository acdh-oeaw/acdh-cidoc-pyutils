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

## development

* `pip install -r requirements_dev.txt`
* `flake8` -> linting
* `coveage run -m pytest` -> runs tests and creates coverage stats