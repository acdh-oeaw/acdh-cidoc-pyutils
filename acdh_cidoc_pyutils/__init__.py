import uuid
import os
from typing import Union

from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, XSD, RDF, RDFS, OWL
from slugify import slugify
from acdh_tei_pyutils.utils import make_entity_label, check_for_hash, extract_fulltext
from acdh_tei_pyutils.tei import TeiReader
from acdh_cidoc_pyutils.namespaces import (
    CIDOC,
    FRBROO,
    SARI_FRBROO,
    NSMAP,
    DATE_ATTRIBUTE_DICT,
    SARI,
    GEO,
)
from acdh_cidoc_pyutils.utils import remove_trailing_slash


def tei_relation_to_SRPC3_in_social_relation(
    node: Element,
    domain="https://foo-bar/",
    lookup_dict={},
    default_type_domain="http://pfp-schema.acdh.oeaw.ac.at/types/person-person/#",
    default_rel_type="In-relation-to",
    lang="de",
    verbose=False,
    entity_prefix="",
) -> Graph:
    """converts a specific TEI relation to SRPC3_in_social_relation

    Args:
        node (Element): A tei:relation element
        domain (str, optional): The domain to build URIs for the related entities. Defaults to "https://foo-bar/".
        lookup_dict (dict, optional): A dict providing mappings from project specific relation types to pfp-types. Defaults to {}.
        default_type_domain (str, optional): The type-domain. Defaults to "http://pfp-schema.acdh.oeaw.ac.at/types/person-person/#".
        default_rel_type (str, optional): A default type which is used if no lookup dict is provided a KeyError is raised. Defaults to "In-relation-to".
        lang (str, optional): The value of the label's lang tag. Defaults to "de".
        entity_prefix (str, optional): Some prefix to add before the IDs of the entities. Defaults to "".
        verbose (bool, optional): Prints if no match in the lookup dict is found. Defaults to False.

    Returns:
        Graph: A Graph object containing the SRPC3_in_social_relation
    """  # noqa: E501
    g = Graph()
    source = f'{entity_prefix}{check_for_hash(node.attrib["active"])}'
    target = f'{entity_prefix}{check_for_hash(node.attrib["passive"])}'
    label = node.attrib["n"]
    rel_type = default_rel_type
    orig_rel_type = node.attrib["name"]
    if lookup_dict:
        try:
            rel_type = lookup_dict[orig_rel_type]
        except KeyError:
            if verbose:
                print(f"Could not find {orig_rel_type} in lookup_dict")
    relation_uri = URIRef(f"{domain}{source}/{rel_type}/{target}")
    g.add((relation_uri, RDF.type, SARI["SRPC3_in_social_relation"]))
    g.add((relation_uri, RDFS.label, Literal(label, lang=lang)))
    g.add(
        (
            relation_uri,
            SARI["SRP3_relation_type"],
            URIRef(f"{default_type_domain}{rel_type}"),
        )
    )
    g.add((relation_uri, CIDOC["P01_has_domain"], URIRef(f"{domain}{source}")))
    g.add((relation_uri, CIDOC["P02_has_range"], URIRef(f"{domain}{target}")))
    return g


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
            Literal(f"Point({lng} {lat})", datatype=GEO["wktLiteral"]),
        )
    )
    return g


def extract_begin_end(
    date_object: Union[Element, dict],
    fill_missing=True,
    attribute_map=DATE_ATTRIBUTE_DICT,
) -> tuple[Union[str, bool], Union[str, bool]]:
    final_start, final_end = None, None
    start, end, when = None, None, None
    for key, value in attribute_map.items():
        date_value = date_object.get(key)
        if date_value and value == "start":
            start = date_value
        if date_value and value == "end":
            end = date_value
        if date_value and value == "when":
            when = date_value
    if fill_missing:
        if start or end or when:
            if start and end:
                final_start, final_end = start, end
            elif start and not end and not when:
                final_start, final_end = start, start
            elif end and not start and not when:
                final_start, final_end = end, end
            elif when and not start and not end:
                final_start, final_end = when, when
            elif when and end and not start:
                final_start, final_end = when, end
    else:
        if start and end:
            final_start, final_end = start, end
        elif start and not end and not when:
            final_start, final_end = start, None
        elif end and not start and not when:
            final_start, final_end = None, end
        elif when and not start and not end:
            final_start, final_end = when, when
        elif when and end and not start:
            final_start, final_end = when, end
    return final_start, final_end


def date_to_literal(
    date_str: Union[str, bool], not_known_value="undefined", default_lang="en"
) -> Literal:
    if date_str is None:
        return_value = Literal(not_known_value, lang=default_lang)
    elif date_str == "":
        return_value = Literal(not_known_value, lang=default_lang)
    else:
        if len(date_str) == 4:
            return_value = Literal(date_str, datatype=XSD.gYear)
        elif len(date_str) == 5 and date_str.startswith("-"):
            return_value = Literal(date_str, datatype=XSD.gYear)
        elif len(date_str) == 7:
            return_value = Literal(date_str, datatype=XSD.gYearMonth)
        elif len(date_str) == 10:
            return_value = Literal(date_str, datatype=XSD.date)
        else:
            return_value = Literal(date_str, datatype=XSD.string)
    return return_value


def make_uri(domain="https://foo.bar/whatever", version="", prefix="") -> URIRef:
    if domain.endswith("/"):
        domain = domain[:-1]
    some_id = f"{uuid.uuid1()}"
    uri_parts = [domain, version, prefix, some_id]
    uri = "/".join([x for x in uri_parts if x != ""])
    return URIRef(uri)


def create_e52(
    uri: URIRef,
    type_uri: Union[URIRef, None] = None,
    begin_of_begin="",
    end_of_end="",
    label=True,
    not_known_value="undefined",
    default_lang="en",
) -> Graph:
    g = Graph()
    g.add((uri, RDF.type, CIDOC["E52_Time-Span"]))
    if begin_of_begin != "":
        g.add(
            (
                uri,
                CIDOC["P82a_begin_of_the_begin"],
                date_to_literal(
                    begin_of_begin,
                    not_known_value=not_known_value,
                    default_lang=default_lang,
                ),
            )
        )
    if end_of_end != "":
        g.add(
            (
                uri,
                CIDOC["P82b_end_of_the_end"],
                date_to_literal(
                    end_of_end,
                    not_known_value=not_known_value,
                    default_lang=default_lang,
                ),
            )
        )
    if end_of_end == "" and begin_of_begin != "":
        g.add(
            (
                uri,
                CIDOC["P82b_end_of_the_end"],
                date_to_literal(
                    begin_of_begin,
                    not_known_value=not_known_value,
                    default_lang=default_lang,
                ),
            )
        )
    if begin_of_begin == "" and end_of_end != "":
        g.add(
            (
                uri,
                CIDOC["P82a_begin_of_the_begin"],
                date_to_literal(
                    end_of_end,
                    not_known_value=not_known_value,
                    default_lang=default_lang,
                ),
            )
        )
    else:
        pass
    if label:
        label_str = " - ".join(
            [
                date_to_literal(
                    begin_of_begin,
                    not_known_value=not_known_value,
                    default_lang=default_lang,
                ),
                date_to_literal(
                    end_of_end,
                    not_known_value=not_known_value,
                    default_lang=default_lang,
                ),
            ]
        ).strip()
        if label_str != "":
            start, end = label_str.split(" - ")
            if start == end:
                g.add((uri, RDFS.label, Literal(start, datatype=XSD.string)))
            else:
                g.add((uri, RDFS.label, Literal(label_str, datatype=XSD.string)))
    if type_uri:
        g.add((uri, CIDOC["P2_has_type"], type_uri))
    return g


def make_appellations(
    subj: URIRef,
    node: Element,
    type_domain="https://foo-bar/",
    type_attribute="type",
    woke_type=False,
    default_lang="de",
    special_xpath=None,
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
    if special_xpath:
        xpath_expression = f"{xpath_expression}{special_xpath}"
    for i, y in enumerate(node.xpath(xpath_expression, namespaces=NSMAP)):
        try:
            lang_tag = y.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        except KeyError:
            lang_tag = default_lang
        type_uri = f"{base_type_uri}/{y.tag.split('}')[-1]}"
        if len(y.xpath("./*")) < 1 and y.text:
            app_uri = URIRef(f"{subj}/appellation/{i}")
            g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
            g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
            g.add(
                (app_uri, RDFS.label, Literal(normalize_string(y.text), lang=lang_tag))
            )
            g.add((app_uri, RDF.value, Literal(normalize_string(y.text))))
            type_label = y.get(type_attribute)
            if type_label:
                cur_type_uri = URIRef(f"{type_uri}/{slugify(type_label)}".lower())
            elif woke_type:
                cur_type_uri = URIRef(f"{type_uri.lower()}/{woke_type}")
            else:
                cur_type_uri = URIRef(type_uri.lower())
            g.add((cur_type_uri, RDF.type, CIDOC["E55_Type"]))
            if type_label:
                g.add(
                    (
                        cur_type_uri,
                        RDFS.label,
                        Literal(f"Appellation of type: {type_label}", lang="en"),
                    )
                )
            else:
                label = f"Appellation of type: {cur_type_uri.split('/')[-1]}'"
                g.add((cur_type_uri, RDFS.label, Literal(label, lang="en")))
            g.add((app_uri, CIDOC["P2_has_type"], cur_type_uri))
        elif len(y.xpath("./*")) > 1:
            app_uri = URIRef(f"{subj}/appellation/{i}")
            g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
            g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
            entity_label_str, cur_lang = make_entity_label(y, default_lang=default_lang)
            g.add(
                (
                    app_uri,
                    RDFS.label,
                    Literal(normalize_string(entity_label_str), lang=cur_lang),
                )
            )
            if woke_type:
                cur_type_uri = URIRef(f"{type_uri.lower()}/{woke_type}")
            else:
                cur_type_uri = URIRef(f"{type_uri.lower()}")
            g.add((cur_type_uri, RDF.type, CIDOC["E55_Type"]))
            label = f"Appellation of type: {cur_type_uri.split('/')[-1]}'"
            g.add((cur_type_uri, RDFS.label, Literal(label, lang="en")))
            g.add((app_uri, CIDOC["P2_has_type"], cur_type_uri))
        else:
            app_uri = URIRef(f"{subj}/appellation")
            g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
            g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
            entity_label_str, cur_lang = make_entity_label(
                node.xpath(xpath_expression, namespaces=NSMAP)[0]
            )
            g.add(
                (
                    app_uri,
                    RDFS.label,
                    Literal(normalize_string(entity_label_str), lang=cur_lang),
                )
            )
            cur_type_uri = URIRef(f"{type_uri.lower()}")
            g.add((cur_type_uri, RDF.type, CIDOC["E55_Type"]))
            label = f"Appellation of type: {cur_type_uri.split('/')[-1]}'"
            g.add((cur_type_uri, RDFS.label, Literal(label, lang="en")))
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


def make_e42_identifiers(
    subj: URIRef,
    node: Element,
    type_domain="https://foo-bar/",
    default_lang="de",
    set_lang=False,
    same_as=True,
    default_prefix="Identifier: ",
) -> Graph:
    """
    Creates RDF triples for E42 Identifiers based on the provided XML node.
    Args:
        subj (URIRef): The subject URIRef to which the identifiers are related.
        node (Element): The XML element containing identifier information.
        type_domain (str, optional): The base URI for the identifier types. Defaults to "https://foo-bar/".
        default_lang (str, optional): The default language for the labels. Defaults to "de".
        set_lang (bool, optional): Whether to set the language for the labels. Defaults to False.
        same_as (bool, optional): Whether to add owl:sameAs triples for HTTP identifiers. Defaults to True.
        default_prefix (str, optional): The prefix for the identifier labels. Defaults to "Identifier: ".
    Returns:
        Graph: An RDF graph containing the generated triples.
    """

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
    label_value = normalize_string(f"{default_prefix}{xml_id}")
    if not type_domain.endswith("/"):
        type_domain = f"{type_domain}/"
    app_uri = URIRef(f"{subj}/identifier/{xml_id}")
    type_uri = URIRef(f"{type_domain}idno/xml-id")
    g.add((type_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((type_uri, RDFS.label, Literal("Identifier: XML-ID", lang="en")))
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
    g.add((app_uri, RDF.type, CIDOC["E42_Identifier"]))
    g.add((app_uri, RDFS.label, Literal(label_value, lang=lang)))
    g.add((app_uri, RDF.value, Literal(normalize_string(xml_id))))
    g.add((app_uri, CIDOC["P2_has_type"], type_uri))
    for i, x in enumerate(node.xpath("./tei:idno", namespaces=NSMAP)):
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
            label = idno_type_base_uri.split("/")[-1]
            g.add(
                (
                    URIRef(idno_type_base_uri),
                    RDFS.label,
                    Literal(
                        f"Identifier of type: '{label}'",
                        lang="en",
                    ),
                )
            )
            label_value = normalize_string(f"{default_prefix}{x.text}")
            g.add((idno_uri, RDFS.label, Literal(label_value, lang=lang)))
            g.add((idno_uri, RDF.value, Literal(normalize_string(x.text))))
            if same_as:
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


def make_occupations(
    subj: URIRef,
    node: Element,
    prefix="occupation",
    id_xpath=False,
    default_lang="de",
    not_known_value="undefined",
    special_label=None,
):
    g = Graph()
    occ_uris = []
    base_uri = f"{subj}/{prefix}"
    for i, x in enumerate(node.xpath(".//tei:occupation", namespaces=NSMAP)):
        try:
            lang = x.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        except KeyError:
            lang = default_lang
        occ_text = normalize_string(" ".join(x.xpath(".//text()")))

        if id_xpath:
            try:
                occ_id = x.xpath(id_xpath, namespaces=NSMAP)[0]
            except IndexError:
                pass
        else:
            occ_id = f"{i}"
        if occ_id.startswith("#"):
            occ_id = occ_id[1:]
        occ_uri = URIRef(f"{base_uri}/{occ_id}")
        occ_uris.append(occ_uri)
        g.add((occ_uri, RDF.type, FRBROO["F51_Pursuit"]))
        if special_label:
            g.add(
                (occ_uri, RDFS.label, Literal(f"{special_label}{occ_text}", lang=lang))
            )
        else:
            g.add((occ_uri, RDFS.label, Literal(occ_text, lang=lang)))
        g.add((subj, CIDOC["P14i_performed"], occ_uri))
        begin, end = extract_begin_end(x, fill_missing=False)
        if begin or end:
            ts_uri = URIRef(f"{occ_uri}/time-span")
            g.add((occ_uri, CIDOC["P4_has_time-span"], ts_uri))
            g += create_e52(
                ts_uri,
                begin_of_begin=begin,
                end_of_end=end,
                not_known_value=not_known_value,
            )
    return (g, occ_uris)


def make_affiliations(
    subj: URIRef,
    node: Element,
    domain: str,
    person_label: str,
    org_id_xpath="./@ref",
    org_label_xpath="",
    lang="en",
    add_org_object=False,
):
    """
    Creates RDF triples representing a person's affiliations with organizations.
    Args:
        subj (URIRef): The URI of the subject (person) whose affiliations are being described.
        node (Element): The XML element containing affiliation information.
        domain (str): The base URI domain for constructing affiliation URIs.
        person_label (str): The label for the person.
        org_id_xpath (str, optional): XPath expression to extract the organization ID. Defaults to "./@ref".
        org_label_xpath (str, optional): XPath expression to extract the organization label. Defaults to "".
        lang (str, optional): Language code for labels. Defaults to "en".
        add_org_object (bool, optional): Whether to add the organization as an object in the graph. Defaults to False.
    Returns:
        Graph: An RDF graph containing the affiliations and related events.
    """
    g = Graph()
    for i, x in enumerate(node.xpath(".//tei:affiliation", namespaces=NSMAP)):
        try:
            affiliation_id = x.xpath(org_id_xpath, namespaces=NSMAP)[0]
        except IndexError:
            continue
        if org_label_xpath == "":
            org_label = normalize_string(" ".join(x.xpath(".//text()")))
        else:
            org_label = normalize_string(
                " ".join(x.xpath(org_label_xpath, namespaces=NSMAP))
            )
        if affiliation_id.startswith("#"):
            affiliation_id = affiliation_id[1:]
        org_affiliation_uri = URIRef(f"{domain}{affiliation_id}")
        if add_org_object:
            g.add((org_affiliation_uri, RDF.type, CIDOC["E74_Group"]))
            g.add((org_affiliation_uri, RDFS.label, Literal(org_label, lang=lang)))
        join_uri = URIRef(f"{subj}/joining/{affiliation_id}/{i}")
        join_label = normalize_string(f"{person_label} joins {org_label}")
        g.add((join_uri, RDF.type, CIDOC["E85_Joining"]))
        g.add((join_uri, CIDOC["P143_joined"], subj))
        g.add((join_uri, CIDOC["P144_joined_with"], org_affiliation_uri))
        g.add((join_uri, RDFS.label, Literal(join_label, lang=lang)))

        begin, end = extract_begin_end(x, fill_missing=False)
        if begin:
            ts_uri = URIRef(f"{join_uri}/time-span/{begin}")
            g.add((join_uri, CIDOC["P4_has_time-span"], ts_uri))
            g += create_e52(ts_uri, begin_of_begin=begin, end_of_end=begin)
        if end:
            leave_uri = URIRef(f"{subj}/leaving/{affiliation_id}/{i}")
            leave_label = normalize_string(f"{person_label} leaves {org_label}")
            g.add((leave_uri, RDF.type, CIDOC["E86_Leaving"]))
            g.add((leave_uri, CIDOC["P145_separated"], subj))
            g.add((leave_uri, CIDOC["P146_separated_from"], org_affiliation_uri))
            g.add((leave_uri, RDFS.label, Literal(leave_label, lang=lang)))
            ts_uri = URIRef(f"{leave_uri}/time-span/{end}")
            g.add((leave_uri, CIDOC["P4_has_time-span"], ts_uri))
            g += create_e52(ts_uri, begin_of_begin=end, end_of_end=end)
    return g


def make_birth_death_entities(
    subj: URIRef,
    node: Element,
    domain: str,
    type_uri: URIRef = None,
    event_type="birth",
    verbose=False,
    default_prefix="Geburt von",
    default_lang="de",
    date_node_xpath="",
    place_id_xpath="//tei:placeName/@key",
):
    g = Graph()
    name_node = node.xpath(".//tei:persName[1]", namespaces=NSMAP)[0]
    label, label_lang = make_entity_label(name_node, default_lang=default_lang)
    if event_type not in ["birth", "death"]:
        return (g, None, None)
    if event_type == "birth":
        cidoc_property = CIDOC["P98_brought_into_life"]
        cidoc_class = CIDOC["E67_Birth"]
    else:
        cidoc_property = CIDOC["P100_was_death_of"]
        cidoc_class = CIDOC["E69_Death"]
    xpath_expr = f".//tei:{event_type}[1]"
    place_xpath = f"{xpath_expr}{place_id_xpath}"
    if date_node_xpath != "":
        date_xpath = f"{xpath_expr}/{date_node_xpath}"
    else:
        date_xpath = xpath_expr
    try:
        node.xpath(xpath_expr, namespaces=NSMAP)[0]
    except IndexError as e:
        if verbose:
            print(subj, e)
            return (g, None, None)
    event_uri = URIRef(f"{subj}/{event_type}")
    g.set((event_uri, cidoc_property, subj))
    g.set((event_uri, RDF.type, cidoc_class))
    g.add(
        (event_uri, RDFS.label, Literal(f"{default_prefix} {label}", lang=label_lang))
    )
    try:
        date_node = node.xpath(date_xpath, namespaces=NSMAP)[0]
        process_date = True
    except IndexError:
        process_date = False
    if process_date:
        time_stamp_uri = URIRef(f"{event_uri}/time-span")
        g.set((event_uri, CIDOC["P4_has_time-span"], time_stamp_uri))
        start, end = extract_begin_end(date_node)
        g += create_e52(time_stamp_uri, type_uri, begin_of_begin=start, end_of_end=end)
    else:
        time_stamp_uri = None
    try:
        place_node = node.xpath(place_xpath, namespaces=NSMAP)[0]
        process_place = True
    except IndexError:
        process_place = False
    if process_place:
        if place_node.startswith("#"):
            place_node = place_node[1:]
        place_uri = URIRef(f"{domain}{place_node}")
        g.add((event_uri, CIDOC["P7_took_place_at"], place_uri))
    return (g, event_uri, time_stamp_uri)


def p89_falls_within(
    subj: URIRef,
    node: Element,
    domain: URIRef,
    location_id_xpath="./tei:location[@type='located_in_place']/tei:placeName/@key",
) -> Graph:
    """connects to places (E53_Place) with P89_falls_within

    Args:
        subj (URIRef): The Uri of the Place
        node (Element): The tei:place Element
        domain (URIRef): An URI used to create the ID of the domain object: {domain}{ID of target object}
        location_id_xpath (str, optional): An XPath expression pointing to the parent's place ID.
        Defaults to "./tei:location[@type='located_in_place']/tei:placeName/@key".

    Returns:
        Graph: A Graph object linking two places via P89_falls_within
    """
    g = Graph()
    try:
        range_id = node.xpath(location_id_xpath, namespaces=NSMAP)[0]
    except IndexError:
        return g
    range_uri = URIRef(f"{domain}{range_id}")
    g.add((subj, CIDOC["P89_falls_within"], range_uri))
    return g


def p95i_was_formed_by(
    uri: URIRef,
    start_date=None,
    end_date=None,
    label="Institution wurde gegründet",
    end_label="Institution wurde aufgelöst",
    label_lang="de",
):
    """
    Create a RDF graph representing the formation event of an institution.
    Args:
        uri (URIRef): The URI of the institution.
        start_date (str, optional): The start date of the formation event. Defaults to None.
        end_date (str, optional): The end date of the formation event. Defaults to None.
        label (str, optional): The label for the formation event. Defaults to "Institution wurde gegründet".
        label_lang (str, optional): The language of the label. Defaults to "de".
    Returns:
        Graph: An RDF graph containing the formation event information.
    """
    g = Graph()
    formation_uri = URIRef(f"{uri}/formation-event")
    g.add((uri, CIDOC["P95i_was_formed_by"], formation_uri))
    g.add((formation_uri, RDF.type, CIDOC["E66_Formation"]))
    g.add((formation_uri, RDFS.label, Literal(label, lang=label_lang)))
    if start_date:
        start_uri = URIRef(f"{formation_uri}/formation-time-span")
        g.add((formation_uri, CIDOC["P4_has_time-span"], start_uri))
        g += create_e52(start_uri, begin_of_begin=start_date, end_of_end=start_date)
    if end_date:
        dissolution_uri = URIRef(f"{uri}/dissolution-event")
        g.add((dissolution_uri, RDF.type, CIDOC["E68_Dissolution"]))
        g.add((dissolution_uri, RDFS.label, Literal(end_label, lang=label_lang)))
        end_uri = URIRef(f"{dissolution_uri}/dissolution-time-span")
        g.add((dissolution_uri, CIDOC["P4_has_time-span"], end_uri))
        g += create_e52(end_uri, begin_of_begin=end_date, end_of_end=end_date)
    return g


def teidoc_as_f24_publication_expression(
    path_to_file: str,
    domain: str,
    title_xpath=".//tei:titleStmt/tei:title[1]",
    mentions_xpath=".//tei:rs[@ref and (@type='person' or @type='place' or @type='org')]",
    add_mentions=True,
    default_lang="de",
    type_uri="https://pfp-schema.acdh.oeaw.ac.at/types/tei-document",
    type_label="A TEI/XML encoded text",
    type_lang="en",
) -> tuple[URIRef, Graph, list]:
    """
    Converts a TEI document into an RDF graph representing a CIDOC CRM F24 Publication Expression.
    Args:
        path_to_file (str): Path to the TEI XML file.
        domain (str): Base URI domain for the generated RDF resources.
        title_xpath (str): XPath expression to extract the title from the TEI document.
        mentions_xpath (str, optional): XPath expression to extract mentions of entities (default is ".//tei:rs[@type='person' or @type='place' or @type='org' and @ref]").
        add_mentions (bool, optional): Whether to add mentions of entities (default is True).
        default_lang (str, optional): Default language for literals (default is "de").
        type_uri (str, optional): URI for the type of the TEI document (default is "https://pfp-schema.acdh.oeaw.ac.at/types/tei-document").
        type_label (str, optional): Label for the type of the TEI document (default is "A TEI/XML encoded text").
        type_lang (str, optional): Language for the type label (default is "en").
    Returns:
        tuple[URIRef, Graph, list]: A tuple containing the URI of the publication expression, the RDF graph and a list of mentioned entity-ids and their type.
    """  # noqa: E501

    domain = remove_trailing_slash(domain)
    g = Graph()
    doc_id = os.path.split(path_to_file)[-1]
    subj = URIRef(f"{domain}/{doc_id}")
    g.add((subj, RDF.type, SARI_FRBROO["F24_Publication_Expression"]))
    doc = TeiReader(path_to_file)

    # title
    title_label = extract_fulltext(doc.any_xpath(title_xpath)[0])
    title_literal = Literal(title_label, lang=default_lang)
    g.add((subj, RDFS.label, title_literal))

    # appellation-type
    app_type_uri = URIRef(type_uri)
    g.add((app_type_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((app_type_uri, RDFS.label, Literal(type_label, lang=type_lang)))

    # appellation
    app_uri = URIRef(f"{subj}/appellation")
    g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
    g.add((app_uri, RDFS.label, title_literal))
    g.add((app_uri, CIDOC["P2_has_type"], app_type_uri))
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))

    # mentions
    mentions = []
    for x in doc.any_xpath(mentions_xpath):
        ref = x.attrib["ref"]
        for y in ref.split(" "):
            type = x.get("type", "unknown")
            mentions.append([check_for_hash(y), type])
    if add_mentions:
        for x in mentions:
            g.add((subj, CIDOC["P67_refers_to"], URIRef(f"{domain}/{x[0]}")))

    return subj, g, mentions
