import uuid
from typing import Union

from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, XSD, RDF, RDFS

from acdh_cidoc_pyutils.namespaces import CIDOC


def normalize_string(string: str) -> str:
    return " ".join(" ".join(string.split()).split())


def extract_begin_end(date_object: Union[Element, dict]) -> tuple[str, str]:
    begin, end = "", ""
    if date_object.get("when-iso", "") != "":
        return (date_object.get("when-iso"), date_object.get("when-iso"))
    elif date_object.get("when", "") != "":
        return (date_object.get("when"), date_object.get("when"))
    begin = date_object.get("notBefore", "")
    end = date_object.get("notAfter", "")
    if begin != "" and end == "":
        end = begin
    if end != "" and begin == "":
        begin = end
    return (begin, end)


def date_to_literal(date_str: str) -> Literal:

    if len(date_str) == 4:
        return Literal(date_str, datatype=XSD.gYear)
    elif len(date_str) == 5 and date_str.startswith("-"):
        return Literal(date_str, datatype=XSD.gYear)
    elif len(date_str) == 7:
        return Literal(date_str, datatype=XSD.gYearMonth)
    elif len(date_str) == 10:
        return Literal(date_str, datatype=XSD.date)
    else:
        return Literal(date_str, datatype=XSD.string)


def make_uri(domain="https://foo.bar/whatever", version="", prefix="") -> URIRef:
    if domain.endswith("/"):
        domain = domain[:-1]
    some_id = f"{uuid.uuid1()}"
    uri_parts = [domain, version, prefix, some_id]
    uri = "/".join([x for x in uri_parts if x != ""])
    return URIRef(uri)


def create_e52(uri: URIRef, begin_of_begin="", end_of_end="", label=True) -> Graph:
    g = Graph()
    g.add((uri, RDF.type, CIDOC["E52_Time-Span"]))
    if begin_of_begin != "":
        g.add((uri, CIDOC["P82a_begin_of_the_begin"], date_to_literal(begin_of_begin)))
    if end_of_end != "":
        g.add((uri, CIDOC["P82b_end_of_the_end"], date_to_literal(end_of_end)))
    if end_of_end == "" and begin_of_begin != "":
        g.add((uri, CIDOC["P82b_end_of_the_end"], date_to_literal(begin_of_begin)))
    if begin_of_begin == "" and end_of_end != "":
        g.add((uri, CIDOC["P82a_begin_of_the_begin"], date_to_literal(end_of_end)))
    else:
        pass
    if label:
        label_str = " - ".join([begin_of_begin, end_of_end]).strip()
        if label_str != "":
            g.add((uri, RDFS.label, Literal(label_str, datatype=XSD.string)))
    return g
