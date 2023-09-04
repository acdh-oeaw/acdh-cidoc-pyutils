import uuid
from typing import Union

from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, XSD, RDF, RDFS, OWL
from slugify import slugify
from acdh_tei_pyutils.utils import make_entity_label
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO, NSMAP, DATE_ATTRIBUTE_DICT


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
    else:
        if start and end:
            final_start, final_end = start, end
        elif start and not end and not when:
            final_start, final_end = start, None
        elif end and not start and not when:
            final_start, final_end = None, end
        elif when and not start and not end:
            final_start, final_end = when, when
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
                g.add((cur_type_uri, RDFS.label, Literal(type_label)))
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
            g.add((app_uri, CIDOC["P2_has_type"], cur_type_uri))
        # see https://github.com/acdh-oeaw/acdh-cidoc-pyutils/issues/36
        # for c, child in enumerate(y.xpath("./*")):
        #     cur_type_uri = f"{type_uri}/{child.tag.split('}')[-1]}".lower()
        #     type_label = child.get(type_attribute)
        #     if type_label:
        #         cur_type_uri = URIRef(f"{cur_type_uri}/{slugify(type_label)}".lower())
        #     else:
        #         cur_type_uri = URIRef(cur_type_uri.lower())
        #     try:
        #         child_lang_tag = child.attrib[
        #             "{http://www.w3.org/XML/1998/namespace}lang"
        #         ]
        #     except KeyError:
        #         child_lang_tag = lang_tag
        #     app_uri = URIRef(f"{subj}/appellation/{i}/{c}")
        #     g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
        #     g.add((app_uri,
        #           RDF.type,
        #           CIDOC["E33_E41_Linguistic_Appellation"]))
        #     g.add(
        #         (
        #             app_uri,
        #             RDFS.label,
        #             Literal(normalize_string(child.text),
        #                       lang=child_lang_tag),
        #         )
        #     )
        #     g.add(
        #         (
        #             app_uri,
        #             RDF.value,
        #             Literal(normalize_string(child.text)),
        #         )
        #     )
        #     g.add((cur_type_uri, RDF.type, CIDOC["E55_Type"]))
        #     if type_label:
        #         g.add((cur_type_uri, RDFS.label, Literal(type_label)))
        #     g.add((app_uri, CIDOC["P2_has_type"], cur_type_uri))
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
    approx_uri = URIRef(f"{type_domain}date/approx")
    g.add((approx_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((approx_uri, RDFS.label, Literal("approx")))
    g.add((type_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
    g.add((app_uri, RDF.type, CIDOC["E42_Identifier"]))
    g.add((app_uri, RDFS.label, Literal(label_value, lang=lang)))
    g.add((app_uri, RDF.value, Literal(normalize_string(xml_id))))
    g.add((app_uri, CIDOC["P2_has_type"], type_uri))
    events_types = {}
    for i, x in enumerate(node.xpath(".//tei:event[@type]", namespaces=NSMAP)):
        events_types[x.attrib["type"]] = x.attrib["type"]
    if events_types:
        for i, x in enumerate(events_types.keys()):
            event_type_uri = URIRef(f"{type_domain}event/{x}")
            g.add((event_type_uri, RDF.type, CIDOC["E55_Type"]))
            g.add((event_type_uri, RDFS.label, Literal(x, lang=default_lang)))
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
    special_label=None
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
            g.add((occ_uri, RDFS.label, Literal(f"{special_label}{occ_text}", lang=lang)))
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
):
    g = Graph()
    xml_id = node.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    item_id = f"{domain}{xml_id}"
    subj = URIRef(item_id)
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
