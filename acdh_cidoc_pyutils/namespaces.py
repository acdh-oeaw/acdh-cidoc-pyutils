from rdflib import Namespace

CIDOC = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
FRBROO = Namespace("http://iflastandards.info/ns/fr/frbr/frbroo#")

NSMAP = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace",
}

DATE_ATTRIBUTE_DICT = {
    "notBefore": "start",
    "notBefore-iso": "start",
    "from": "start",
    "from-iso": "start",
    "notAfter": "end",
    "notAfter-iso": "end",
    "to": "end",
    "to-iso": "end",
    "when": "when",
    "when-iso": "when"
}
