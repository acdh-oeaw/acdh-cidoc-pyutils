import os
import unittest

import lxml.etree as ET
from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import get_xmlid
from lxml.etree import Element
from rdflib import RDF, Graph, URIRef

from acdh_cidoc_pyutils import (
    coordinates_to_p168,
    create_e52,
    date_to_literal,
    extract_begin_end,
    make_affiliations,
    make_appellations,
    make_birth_death_entities,
    make_e42_identifiers,
    make_occupations,
    make_uri,
    normalize_string,
    p89_falls_within,
    p95i_was_formed_by,
    tei_relation_to_SRPC3_in_social_relation,
    teidoc_as_f24_publication_expression,
)
from acdh_cidoc_pyutils.namespaces import CIDOC, NSMAP
from acdh_cidoc_pyutils.utils import remove_trailing_slash

sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0091" sortKey="Gulbransson_Olaf_Leonhard">
        <persName xml:lang="fr">
            <forename>Olaf</forename>
            <forename type="unused" xml:lang="bg">Leonhard</forename>
            <surname>Gulbransson</surname>
        </persName>
        <birth when="1873-05-26">26. 5. 1873<placeName key="#DWplace00139"
                >Christiania (Oslo)</placeName></birth>
        <death>
            <date notBefore-iso="1905-07-04" when="1955" to="2000">04.07.1905</date>
            <settlement key="pmb50">
                <placeName type="pref">Wien</placeName>
                <location><geo>48.2066 16.37341</geo></location>
            </settlement>
        </death>
        <persName type="pref">Gulbransson, Olaf</persName>
        <persName type="full">Gulbransson, Olaf Leonhard</persName>
        <occupation type="prim" n="01">Zeichner und Maler</occupation>
        <occupation notBefore="1902" notAfter="1944" n="02">Mitarbeiter des <title
                level="j">Simplicissimus</title></occupation>
        <idno type="GND">118543539</idno>
    </person>
    <place xml:id="DWplace00092">
        <placeName type="orig_name">Reval (Tallinn)</placeName>
        <placeName xml:lang="de" type="simple_name">Reval</placeName>
        <placeName xml:lang="und" type="alt_label">Tallinn</placeName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/42085/</idno>
        <idno type="pmb">https://foo-bar-hansi-sumsi/</idno>
        <idno type="URI" subtype="geonames">https://www.geonames.org/588409</idno>
        <idno subtype="foobarid">12345</idno>
        <location><geo>123 456</geo></location>
    </place>
    <place xml:id="DWplace00010">
        <placeName xml:lang="de" type="orig_name">Jaworzno</placeName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/94280/</idno>
        <location><geo>123 456 789</geo></location>
    </place>
    <org xml:id="DWorg00001">
        <orgName xml:lang="de" type="orig_name">Stahlhelm</orgName>
        <orgName xml:lang="de" type="short">Stahlhelm</orgName>
        <orgName xml:lang="de" type="full">Stahlhelm, Bund der Frontsoldaten</orgName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/135089/</idno>
        <idno type="gnd">https://d-nb.info/gnd/63616-2</idno>
    </org>
    <org xml:id="DWorg00002">
        <orgName xml:lang="de" type="orig_name">GDVP</orgName>
        <orgName xml:lang="de" type="short">GDVP</orgName>
        <orgName xml:lang="de" type="full">Großdeutsche Volkspartei</orgName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/135090/</idno>
        <idno type="gnd">https://d-nb.info/gnd/410560-6</idno>
    </org>
    <place xml:id="DWplace00013">
        <placeName type="orig_name">Radebeul (?)</placeName>
        <placeName xml:lang="de">Radebeul</placeName>
        <placeName xml:lang="und" type="alt_label"></placeName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/45569/</idno>
    </place>
    <bibl xml:id="DWbible01113">
        <title>Hansi4ever</title>
    </bibl>
    <bibl xml:id="superduperbibl">
        <title>Superduper</title>
    </bibl>
    <person xml:id="hansi12343">
        <test></test>
    </person>
    <person xml:id="onlypersnameelement">
        <persName>Ronja, Hanna</persName>
    </person>
    <person xml:id="maxicosi">
        <persName><forename>maxi</forename><surname>cosi</surname></persName>
    </person>
</TEI>
"""


DATE_STRINGS = ["1900", "-1900", "1900-01", "1901-01-01", "foo", "", None, "-389"]
DATE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#gYear",
    "http://www.w3.org/2001/XMLSchema#gYear",
    "http://www.w3.org/2001/XMLSchema#gYearMonth",
    "http://www.w3.org/2001/XMLSchema#date",
    "http://www.w3.org/2001/XMLSchema#string",
    "None",
    "None",
    "http://www.w3.org/2001/XMLSchema#gYear",
]


class TestTestTest(unittest.TestCase):
    """Tests for `acdh_cidoc_pyutils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_trailing_slash(self):
        uri = "foo/bar/"
        self.assertEqual("foo/bar", remove_trailing_slash(uri))
        uri = "foo/bar"
        self.assertEqual("foo/bar", remove_trailing_slash(uri))

    def test_002_dates(self):
        for i, x in enumerate(DATE_STRINGS):
            date_literal = date_to_literal(x)
            self.assertEqual(f"{date_literal.datatype}", DATE_TYPES[i])

    def text_002a_four_digit_year(self):
        sample = "-389"
        self.assertEqual(sample, f"{date_to_literal(sample)}")

    def test_003_make_uri(self):
        domain = "https://hansi4ever.com/"
        version = "1"
        prefix = "sumsi"
        uri = make_uri(domain=domain, version=version, prefix=prefix)
        for x in [domain, version, prefix]:
            self.assertTrue(x in f"{uri}")

    def test_004_create_e52(self):
        uri = make_uri()
        begin_of_begin = "1234-05-06"
        e52 = create_e52(uri)
        self.assertTrue(isinstance(e52, Graph))
        e52 = create_e52(uri, begin_of_begin=begin_of_begin)
        graph_string = f"{e52.serialize()}"
        self.assertTrue(begin_of_begin in graph_string)
        e52 = create_e52(uri, end_of_end=begin_of_begin)
        self.assertTrue(begin_of_begin in graph_string)
        e52 = create_e52(uri, begin_of_begin=begin_of_begin, end_of_end=begin_of_begin)
        e52.serialize("e52.ttl")
        self.assertTrue('rdfs:label "1234-05-06"^^xsd:string' in f"{e52.serialize()}")
        e52 = create_e52(uri, begin_of_begin="1222", end_of_end=begin_of_begin)
        e52.serialize("e52.ttl")
        self.assertFalse('rdfs:label "1234-05-06"^^xsd:string' in f"{e52.serialize()}")
        e52.serialize("e521.ttl")

    def test_005_normalize_string(self):
        string = """\n\nhallo
mein schatz ich liebe    dich
    du bist         die einzige für mich
        """
        normalized = normalize_string(string)
        self.assertTrue("\n" not in normalized)

    def test_006_begin_end(self):
        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["when-iso"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertEqual(begin, date_string)
        self.assertEqual(end, date_string)
        begin, end = extract_begin_end(date_object, fill_missing=False)
        self.assertEqual(begin, date_string)
        self.assertEqual(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["from-iso"] = date_string
        begin, end = extract_begin_end(date_object, fill_missing=False)
        self.assertEqual(begin, date_string)
        self.assertEqual(end, None)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["when"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertEqual(begin, date_string)
        self.assertEqual(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notAfter"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertEqual(begin, date_string)
        self.assertEqual(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notBefore"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertEqual(begin, date_string)
        self.assertEqual(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notAfter"] = date_string
        date_object.attrib["notBefore"] = "1800"
        begin, end = extract_begin_end(date_object)
        self.assertEqual(begin, "1800")
        self.assertEqual(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notAfter"] = date_string
        date_object.attrib["notBefore"] = "1800"
        begin, end = extract_begin_end(date_object, fill_missing=False)
        self.assertEqual(begin, "1800")
        self.assertEqual(end, date_string)
        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["to"] = date_string
        begin, end = extract_begin_end(date_object, fill_missing=False)
        self.assertEqual(begin, None)
        self.assertEqual(end, date_string)

    def test_007_make_appellations(self):
        g = Graph()
        doc = ET.fromstring(sample)
        for x in doc.xpath(
            ".//tei:place|tei:org|tei:person|tei:bibl", namespaces=NSMAP
        ):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_appellations(
                subj,
                x,
                type_domain="https://sk.acdh.oeaw.ac.at/types",
                default_lang="it",
            )
        data = g.serialize(format="turtle")
        g.serialize("appellation.ttl", format="turtle")
        self.assertTrue('rdfs:label "Stahlhelm, Bund der Frontsoldaten"@de' in data)
        self.assertTrue('rdf:value "Stahlhelm, Bund der Frontsoldaten"' in data)
        self.assertTrue("@it" in data)
        self.assertTrue('dfs:label "Gulbransson, Olaf"' in data)
        self.assertTrue('rdfs:label "cosi, maxi"@it' in data)
        self.assertTrue("Superduper" in data)

    def test_007a_make_appellations(self):
        g = Graph()
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="person__244261">
        <persName>
            <surname>Friedrich VII. von Baden-Durlach</surname>
        </persName>
    </person>
</TEI>
"""
        doc = TeiReader(sample)
        node = doc.any_xpath(".//tei:person")[0]
        xml_id = get_xmlid(node)
        subj = URIRef(f"https://foo.bar/{xml_id}")
        g.add((subj, RDF.type, CIDOC["E21_Person"]))
        g += make_appellations(subj, node)
        data = g.serialize(format="turtle")
        self.assertTrue("Friedrich VII. von Baden-Durlach" in data)
        self.assertTrue("appellation" in data)
        g.serialize("surname.ttl", format="turtle")

    def test_008_make_e42_identifiers(self):
        g = Graph()
        doc = ET.fromstring(sample)
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_e42_identifiers(
                subj,
                x,
                type_domain="https://sk.acdh.oeaw.ac.at/types",
                default_lang="it",
            )
            data = g.serialize(format="turtle")
        g = Graph()
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_e42_identifiers(
                subj,
                x,
                type_domain="https://sk.acdh.oeaw.ac.at/types",
                default_lang="it",
                authority_patterns=[],
                set_lang=True,
            )
            data = g.serialize(format="turtle")
            self.assertTrue("@it" in data)
            self.assertTrue("idno/foobarid" in data)
            self.assertTrue("owl:sameAs <https://" in data)
            self.assertTrue("https://foo-bar-hansi-sumsi/" in data)
            g.serialize("ids.ttl", format="turtle")
        g = Graph()
        default_prefix = "sumsibumsi 123: "
        match_value = 'rdf:value "DWpl'
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_e42_identifiers(
                subj,
                x,
                type_domain="https://sk.acdh.oeaw.ac.at/types",
                default_lang="it",
                set_lang=True,
                same_as=False,
                default_prefix=default_prefix,
            )
            data = g.serialize(format="turtle")
            self.assertTrue("@it" in data)
            self.assertTrue("idno/foobarid" in data)
            self.assertTrue(default_prefix in data)
            self.assertFalse("owl:sameAs <https://" in data)
            self.assertTrue(match_value in data)
            g.serialize("ids1.ttl", format="turtle")

        g = Graph()
        default_prefix = "sumsibumsi 123: "
        match_value = 'rdf:value "DWpl'
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_e42_identifiers(
                subj,
                x,
                type_domain="https://sk.acdh.oeaw.ac.at/types",
                default_lang="it",
                set_lang=True,
                same_as=True,
                default_prefix=default_prefix,
            )
            data = g.serialize(format="turtle")
            self.assertFalse("owl:sameAs <https://foo-bar-hansi-sumsi/>" in data)
            # self.assertTrue("@it" in data)
            self.assertTrue("idno/foobarid" in data)
            self.assertTrue(default_prefix in data)
            self.assertTrue("owl:sameAs <https://" in data)
            self.assertTrue(match_value in data)
            g.serialize("ids3.ttl", format="turtle")

    def test_009_coordinates(self):
        doc = ET.fromstring(sample)
        g = Graph()
        for x in doc.xpath(".//tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += coordinates_to_p168(subj, x)
        data = g.serialize(format="turtle")
        self.assertTrue("Point(456 123)" in data)
        g.serialize("coords.ttl", format="turtle")

        g = Graph()
        for x in doc.xpath(".//tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += coordinates_to_p168(subj, x, inverse=True, verbose=True)
        data = g.serialize(format="turtle")
        self.assertTrue("Point(123 456)" in data)
        g.serialize("coords1.ttl", format="turtle")

    def test_010_birth_death(self):
        doc = ET.fromstring(sample)
        x = doc.xpath(".//tei:person[1]", namespaces=NSMAP)[0]
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
        item_id = f"https://foo/bar/{xml_id}"
        subj = URIRef(item_id)
        event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
            subj, x, domain="https://foo/bar/", verbose=False
        )
        event_graph.serialize("birth.ttl")
        self.assertTrue(isinstance(event_graph, Graph))
        for uri in [birth_uri, birth_timestamp]:
            self.assertTrue(isinstance(uri, URIRef))
        event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
            subj, x, domain="https://foo/bar/", event_type="hansi4ever", verbose=True
        )
        for uri in [birth_uri, birth_timestamp]:
            self.assertTrue((uri, None))
        event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
            subj,
            x,
            domain="https://foo/bar/",
            event_type="death",
            verbose=True,
            date_node_xpath="/tei:date[1]",
            place_id_xpath="//tei:settlement[1]/@key",
        )
        event_graph.serialize("death.ttl")
        event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
            subj,
            x,
            domain="https://foo/bar/",
            event_type="death",
            verbose=True,
            date_node_xpath="/tei:nonsense[1]",
            place_id_xpath="//tei:settlement[1]/@key",
        )
        for bad in x.xpath(".//tei:death", namespaces=NSMAP):
            bad.getparent().remove(bad)
        event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
            subj,
            x,
            domain="https://foo/bar/",
            event_type="death",
            verbose=True,
        )
        new_sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0091" sortKey="Gulbransson_Olaf_Leonhard">
        <persName type="pref">Gulbransson, Olaf</persName>
        <birth>
            26. 5. 1873<placeName key="#DWplace00139">Christiania (Oslo)</placeName>
        </birth>
        <death>
            <date notBefore-iso="1905-07-04" when="1955" to="2000">04.07.1905</date>
            <settlement key="pmb50">
                <placeName type="pref">Wien</placeName>
                <location><geo>48.2066 16.37341</geo></location>
            </settlement>
        </death>
    </person>
</TEI>"""

        doc = ET.fromstring(new_sample)
        x = doc.xpath(".//tei:person[1]", namespaces=NSMAP)[0]
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        item_id = f"https://foo/bar/{xml_id}"
        subj = URIRef(item_id)
        event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
            subj,
            x,
            domain="https://foo/bar/",
            verbose=False,
            place_id_xpath="//tei:nonsense[1]/@key",
        )
        event_graph.serialize("no_date.ttl")

    def test_011_occupation(self):
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0091" sortKey="Gulbransson_Olaf_Leonhard">
        <persName type="pref">Gulbransson, Olaf</persName>
        <occupation notBefore="1900-12" notAfter="2000" key="#hansi" xml:lang="it">Bürgermeister</occupation>
        <occupation from="1233-02-03" key="#sumsi">Tischlermeister/Fleischhauer</occupation>
        <occupation key="franzi">Sängerin</occupation>
        <occupation>Bäckerin</occupation>
    </person>
</TEI>"""
        doc = ET.fromstring(sample)
        x = doc.xpath(".//tei:person[1]", namespaces=NSMAP)[0]
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        item_id = f"https://foo/bar/{xml_id}"
        subj = URIRef(item_id)
        g, uris = make_occupations(subj, x)
        self.assertFalse("occupation/hansi" in g.serialize(format="turtle"))
        g.serialize("occupations.ttl")
        g1, uris = make_occupations(
            subj, x, id_xpath="@key", not_known_value="ronjaundhanna"
        )
        g1.serialize("occupations1.ttl")
        self.assertTrue("occupation/hansi" in g1.serialize(format="turtle"))
        self.assertTrue("ronjaundhanna" in g1.serialize(format="turtle"))

    def test_012_affiliations(self):
        domain = "https://foo/bar/"
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0091" sortKey="Gulbransson_Olaf_Leonhard">
        <persName type="pref">Gulbransson, Olaf</persName>
        <affiliation notBefore="1900" notAfter="1931">No ref

        </affiliation>
        <affiliation notBefore="1900" notAfter="1931" ref="DWorg00010" n="01">SPD</affiliation>
        <affiliation notBefore="1931" ref="#DWorg00009" n="hansi">SAPD</affiliation>
        <affiliation notBefore="1938" notAfter="1945-01-02" ref="#DWorg00010" n="03">SPD</affiliation>
    </person>
</TEI>"""
        person_label = """Gulbransson,

        Olaf"""
        doc = ET.fromstring(sample)
        x = doc.xpath(".//tei:person[1]", namespaces=NSMAP)[0]
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        item_id = f"{domain}{xml_id}"
        subj = URIRef(item_id)
        g = make_affiliations(subj, x, domain, person_label=person_label)
        g.serialize("affiliations.ttl")

        domain = "https://foo/bar/"
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0091" sortKey="Gulbransson_Olaf_Leonhard">
        <persName type="pref">Gulbransson, Olaf</persName>
        <affiliation notBefore-iso="1904-01-01" when-iso="1904-07-01" notAfter-iso="1904-12-31">
            <term key="1153">in Bezug zu</term>
            <orgName key="pmb46027">Akademisches Gymnasium Wien</orgName>
        </affiliation>
        <affiliation>
            <term key="1182">arbeitet für</term>
            <orgName key="pmb51868">Cabaret Fledermaus</orgName>
        </affiliation>
        <affiliation notAfter="1922">
            <term key="1234">arbeitet für</term>
            <orgName key="pmb518681">Schule</orgName>
        </affiliation>
    </person>
</TEI>"""
        person_label = "Gulbransson, Olaf"
        doc = ET.fromstring(sample)
        x = doc.xpath(".//tei:person[1]", namespaces=NSMAP)[0]
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        item_id = f"{domain}{xml_id}"
        subj = URIRef(item_id)
        g = make_affiliations(
            subj,
            x,
            domain,
            person_label=person_label,
            org_id_xpath="./tei:orgName[1]/@key",
            org_label_xpath="./tei:orgName[1]//text()",
            add_org_object=True,
        )
        result = g.serialize(format="ttl")
        self.assertTrue("<https://foo/bar/pmb51868> a ns1:E74_Group ;" in result)
        g.serialize("affiliations1.ttl")

    def test_013_p89_falls_within(self):
        domain = "https://foo/bar/"
        subj = URIRef(f"{domain}place__237979")
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <place xml:id="place__237979">
        <placeName>Lerchenfelder G&#252;rtel 48</placeName>
        <desc type="entity_type">Wohngeb&#228;ude (K.WHS)</desc>
        <desc type="entity_type_id">36</desc>
        <location type="coords">
            <geo>48,209035 16,339257</geo>
        </location>
        <location>
            <placeName ref="place__50">Wien</placeName>
            <geo>48,208333 16,373056</geo>
        </location>
    </place>
</TEI>"""
        doc = ET.fromstring(sample)
        node = doc.xpath(".//tei:place[1]", namespaces=NSMAP)[0]
        g = p89_falls_within(
            subj, node, domain, location_id_xpath="./tei:location/tei:placeName/@ref"
        )
        result = g.serialize(format="ttl")
        self.assertTrue("https://foo/bar/place__50" in result)
        g.serialize("p89.ttl")

        g = p89_falls_within(
            subj, node, domain, location_id_xpath="./tei:location/tei:placeName/@key"
        )
        result = g.serialize(format="ttl")
        self.assertFalse("https://foo/bar/place__50" in result)

    def test_014_tei_relation_to_SRPC3(self):
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <listRelation>
    <relation name="ist-verheiratet-mit" active="#21208" passive="#24420"
        from-iso="1936-01-01" n="Schnitzler, Hans — ist verheiratet mit — Mautner, Lisa"/>
    <relation name="ist-asdfverheiratet-mit" active="#21208" passive="#24420"
        n="Schnitzler, Hans — ist verheiratet mit — Mautner, Lisa"/>
    <relation name="ist-verlobt-mit" active="#21208" passive="#24420"
        n="Schnitzler, Hans — ist verheiratet mit — Mautner, Lisa"/>
    <relation name="in-intimer-beziehung-zu" active="#pmb28964" passive="#pmb38513"
        from-iso="1932-01-01" to-iso="1942-01-01"
        n="Viertel, Salka — in intimer Beziehung zu — Reinhardt, Gottfried"/>
    </listRelation>
</TEI>"""
        g = Graph()
        lookup_dict = {
            "in-intimer-beziehung-zu": "Intimate-relation",
            "ist-verlobt-mit": "https://hansi/sumsi/#Is-engaged-to",
            "ist-verheiratet-mit": "https://hansi/sumsi/Is-married-to",
        }
        doc = ET.fromstring(sample)
        for x in doc.xpath(".//tei:relation", namespaces=NSMAP):
            g += tei_relation_to_SRPC3_in_social_relation(
                x,
                domain="https://pmb.acdh.oeaw.ac.at/entity/",
                lookup_dict=lookup_dict,
                verbose=True,
                entity_prefix="person_",
            )
        result = g.serialize(format="ttl")
        g.serialize("relations.ttl", format="ttl")
        self.assertTrue("Is-married-to" in result)
        self.assertTrue("In-relation-to" in result)
        for x in doc.xpath(".//tei:relation", namespaces=NSMAP):
            g += tei_relation_to_SRPC3_in_social_relation(
                x,
                domain="https://pmb.acdh.oeaw.ac.at/entity/",
                lookup_dict=lookup_dict,
                verbose=False,
            )

    def test_015_p95i_was_formed_by(self):
        g = Graph()
        subj = URIRef("https://www.wikidata.org/wiki/Q392310")
        label = "LASK Linz"
        g += p95i_was_formed_by(
            subj,
            start_date="1908-07-25",
            label=f"{label} wurde gegründet",
            label_lang="de",
        )
        result = g.serialize(format="ttl")
        g.serialize("E66_Formation.ttl", format="ttl")
        self.assertTrue("P95i_was_formed_by" in result)

        g = Graph()
        subj = URIRef("https://wienerschnitzler.org")
        label = "Wiener Moderne Verein"
        g += p95i_was_formed_by(
            subj,
            start_date="2023-10-14",
            end_date="2025-12-31",
            label=f"{label} wurde gegründet",
            label_lang="de",
        )
        result = g.serialize(format="ttl")
        g.serialize("E68_Dissolution.ttl", format="ttl")
        self.assertTrue("aufgelöst" in result)

    def test_016_teidoc_as_f24_publication_expression(self):
        file_name = "L02643.xml"
        domain = "https://schnitzler-briefe.acdh.oeaw.ac.at"
        file_path = os.path.join("tests", file_name)
        _, g, _ = teidoc_as_f24_publication_expression(
            file_path, domain, ".//tei:titleStmt/tei:title[@level='a']"
        )
        g.serialize(file_name.replace(".xml", ".ttl"))
        result = g.serialize(format="ttl")
        self.assertTrue("P1_is_identified_by" in result)
        _, g, _ = teidoc_as_f24_publication_expression(
            file_path,
            domain,
            ".//tei:titleStmt/tei:title[@level='a']",
            add_mentions=False,
        )
        g.serialize(file_name.replace(".xml", "no-mentions.ttl"))
        result = g.serialize(format="ttl")
        self.assertTrue("P1_is_identified_by" in result)

    def test_017_normalize_sameas(self):
        sample = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <person xml:id="person__244261">
                <persName>
                    <surname>Friedrich VII. von Baden-Durlach</surname>
                </persName>
                <idno type="GND">http://d-nb.info/gnd/101791799X</idno>
            </person>
        </TEI>
        """
        g = Graph()
        doc = TeiReader(sample)
        for x in doc.any_xpath(".//tei:person"):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_e42_identifiers(
                subj,
                x,
                type_domain="https://sk.acdh.oeaw.ac.at/types",
            )
        g.serialize("normalized.ttl")
        result = g.serialize(format="ttl")
        self.assertTrue("https://d-nb.info/gnd/101791799X" in result)
