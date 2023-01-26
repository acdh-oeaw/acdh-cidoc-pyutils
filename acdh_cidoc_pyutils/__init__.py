import uuid
from typing import Union

from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, XSD, RDF, RDFS, OWL
from slugify import slugify
from acdh_tei_pyutils.utils import make_entity_label
from acdh_cidoc_pyutils.namespaces import CIDOC, NSMAP


def normalize_string(string: str) -> str:
    return " ".join(" ".join(string.split()).split())


def coordinates_to_p168(
    subj: URIRef,
    node: Element,
    coords_xpath=".//tei:geo[1]",
    separator=" ",
    inverse=False,
    verbose=False,
) -> Graph:
    g = Graph()
    try:
        coords = node.xpath(coords_xpath, namespaces=NSMAP)[0]
    except IndexError as e:
        if verbose:
            print(e, subj)
        return g
    try:
        lat, lng = coords.text.split(separator)
    except (ValueError, AttributeError) as e:
        if verbose:
            print(e, subj)
        return g
    if inverse:
        lat, lng = lng, lat
    g.set(
        (
            subj,
            CIDOC["P168_place_is_defined_by"],
            Literal(f"Point({lng} {lat})", datatype="geo:wktLiteral"),
        )
    )
    return g


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
    tag_name = node.tag.split("}")[-1]
    base_type_uri = f"{type_domain}{tag_name}"
    if tag_name.endswith("place"):
        xpath_expression = ".//tei:placeName"
    elif tag_name.endswith("person"):
        xpath_expression = ".//tei:persName"
    elif tag_name.endswith("org"):
        xpath_expression = ".//tei:orgName"
    else:
        return g
    for i, y in enumerate(node.xpath(xpath_expression, namespaces=NSMAP)):
        try:
            lang_tag = y.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        except KeyError:
            lang_tag = default_lang
        type_uri = f"{base_type_uri}/{y.tag.split('}')[-1]}"
        if len(y.xpath("./*")) < 1 and y.text:
            app_uri = URIRef(f"{subj}/appelation/{i}")
            g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
            g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
            g.add(
                (app_uri, RDFS.label, Literal(normalize_string(y.text), lang=lang_tag))
            )
            type_label = y.get(type_attribute)
            if type_label:
                cur_type_uri = URIRef(f"{type_uri}/{slugify(type_label)}".lower())
            else:
                cur_type_uri = URIRef(type_uri.lower())
            g.add((cur_type_uri, RDF.type, CIDOC["E55_Type"]))
            if type_label:
                g.add((cur_type_uri, RDFS.label, Literal(type_label)))
            g.add((app_uri, CIDOC["P2_has_type"], cur_type_uri))
        for c, child in enumerate(y.xpath("./*")):
            cur_type_uri = f"{type_uri}/{child.tag.split('}')[-1]}".lower()
            type_label = child.get(type_attribute)
            if type_label:
                cur_type_uri = URIRef(f"{cur_type_uri}/{slugify(type_label)}".lower())
            else:
                cur_type_uri = URIRef(cur_type_uri.lower())
            try:
                child_lang_tag = child.attrib[
                    "{http://www.w3.org/XML/1998/namespace}lang"
                ]
            except KeyError:
                child_lang_tag = lang_tag
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
            g.add((cur_type_uri, RDF.type, CIDOC["E55_Type"]))
            if type_label:
                g.add((cur_type_uri, RDFS.label, Literal(type_label)))
            g.add((app_uri, CIDOC["P2_has_type"], cur_type_uri))
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
    set_lang=False,
) -> Graph:
    g = Graph()
    try:
        lang = node.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
    except KeyError:
        lang = default_lang
    if set_lang:
        pass
    else:
        lang = "und"
    xml_id = node.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    if not type_domain.endswith("/"):
        type_domain = f"{type_domain}/"
    app_uri = URIRef(f"{subj}/identifier/{xml_id}")
    type_uri = URIRef(f"{type_domain}xml-id")
    g.add((type_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
    g.add((app_uri, RDF.type, CIDOC["E42_Identifier"]))
    g.add((app_uri, RDFS.label, Literal(xml_id, lang=lang)))
    g.add((app_uri, CIDOC["P2_has_type"], type_uri))
    for i, x in enumerate(node.xpath(".//tei:idno", namespaces=NSMAP)):
        idno_type_base_uri = f"{type_domain}idno"
        if x.text:
            idno_uri = URIRef(f"{subj}/identifier/idno/{i}")
            g.add((subj, CIDOC["P1_is_identified_by"], idno_uri))
            idno_type = x.get("type")
            if idno_type:
                idno_type_base_uri = f"{idno_type_base_uri}/{idno_type}"
            idno_type = x.get("subtype")
            if idno_type:
                idno_type_base_uri = f"{idno_type_base_uri}/{idno_type}"
            g.add((idno_uri, RDF.type, CIDOC["E42_Identifier"]))
            g.add((idno_uri, CIDOC["P2_has_type"], URIRef(idno_type_base_uri)))
            g.add((URIRef(idno_type_base_uri), RDF.type, CIDOC["E55_Type"]))
            g.add((idno_uri, RDFS.label, Literal(x.text, lang=lang)))
            if x.text.startswith("http"):
                g.add(
                    (
                        subj,
                        OWL.sameAs,
                        URIRef(
                            x.text,
                        ),
                    )
                )
    return g
