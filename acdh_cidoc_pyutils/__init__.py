import uuid
from typing import Union

from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, XSD, RDF, RDFS
from slugify import slugify
from acdh_tei_pyutils.utils import make_entity_label
from acdh_cidoc_pyutils.namespaces import CIDOC, NSMAP


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


def make_appelations(
    subj: URIRef,
    node: Element,
    type_domain="https://foo-bar/",
    type_attribute="type",
    default_lang="de",
) -> Graph:
    if not type_domain.endswith("/"):
        type_domain = f"{type_domain}/"
    g = Graph()
    tag_name = node.tag
    if tag_name.endswith("place"):
        xpath_expression = ".//tei:placeName"
    elif tag_name.endswith("person"):
        xpath_expression = ".//tei:persName"
    elif tag_name.endswith("org"):
        xpath_expression = ".//tei:orgName"
    else:
        return g
    for i, y in enumerate(node.xpath(xpath_expression, namespaces=NSMAP)):
        name_tag = y.tag.split("}")[-1]
        try:
            lang_tag = y.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        except KeyError:
            lang_tag = default_lang
        if len(y.xpath("./*")) < 1 and y.text:
            app_uri = URIRef(f"{subj}/appelation/{i}")
            g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
            g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
            g.add(
                (app_uri, RDFS.label, Literal(normalize_string(y.text), lang=lang_tag))
            )
            has_type = y.get(type_attribute)
            if has_type:
                type_uri = URIRef(f"{type_domain}{slugify(has_type)}")
                g.add((type_uri, RDF.type, CIDOC["E55_Type"]))
                g.add((type_uri, RDFS.label, Literal(has_type)))
                g.add((app_uri, CIDOC["P2_has_type"], type_uri))
        for c, child in enumerate(y.xpath("./*")):
            try:
                child_lang_tag = child.attrib[
                    "{http://www.w3.org/XML/1998/namespace}lang"
                ]
            except KeyError:
                child_lang_tag = lang_tag
            child_tag_name = child.tag.split("}")[-1]
            has_type = child.get(type_attribute)
            app_uri = URIRef(f"{subj}/appelation/{i}/{c}")
            g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
            g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
            g.add(
                (
                    app_uri,
                    RDFS.label,
                    Literal(normalize_string(child.text), lang=child_lang_tag),
                )
            )
            has_type = child.get(type_attribute)
            if has_type:
                type_uri = URIRef(
                    f"{type_domain}{tag_name.split('}')[-1]}-{name_tag}-{child_tag_name}-{slugify(has_type)}"
                )
            else:
                type_uri = URIRef(
                    f"{type_domain}{tag_name.split('}')[-1]}-{name_tag}-{child_tag_name}"
                )
            g.add((type_uri, RDF.type, CIDOC["E55_Type"]))
            g.add((type_uri, RDFS.label, Literal(has_type)))
            g.add((app_uri, CIDOC["P2_has_type"], type_uri))
    try:
        first_name_el = node.xpath(xpath_expression, namespaces=NSMAP)[0]
    except IndexError:
        return g
    entity_label_str, cur_lang = make_entity_label(
        first_name_el, default_lang=default_lang
    )
    g.add((subj, RDFS.label, Literal(entity_label_str, lang=cur_lang)))
    return g


def make_ed42_identifiers(
    subj: URIRef,
    node: Element,
    type_domain="https://foo-bar/",
    default_lang="de",
) -> Graph:
    g = Graph()
    try:
        lang = node.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
    except KeyError:
        lang = default_lang
    xml_id = node.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    if not type_domain.endswith("/"):
        type_domain = f"{type_domain}/"
    app_uri = URIRef(f"{subj}/identifier/{xml_id}")
    type_uri = URIRef(f"{type_domain}xml-id")
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
    g.add((app_uri, RDF.type, CIDOC["E42_Identifier"]))
    g.add((app_uri, RDFS.label, Literal(xml_id, lang=lang)))
    g.add((app_uri, CIDOC["P2_has_type"], type_uri))
    return g
