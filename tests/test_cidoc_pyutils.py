import unittest
import lxml.etree as ET

from lxml.etree import Element
from rdflib import Graph, URIRef, RDF

from acdh_cidoc_pyutils import (
    date_to_literal,
    make_uri,
    create_e52,
    normalize_string,
    extract_begin_end,
    make_appellations,
    make_e42_identifiers,
    coordinates_to_p168,
    make_birth_death_entities,
    make_occupations,
    make_affiliations,
    make_events,
)
from acdh_cidoc_pyutils.namespaces import NSMAP, CIDOC

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


DATE_STRINGS = ["1900", "-1900", "1900-01", "1901-01-01", "foo", "", None]
DATE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#gYear",
    "http://www.w3.org/2001/XMLSchema#gYear",
    "http://www.w3.org/2001/XMLSchema#gYearMonth",
    "http://www.w3.org/2001/XMLSchema#date",
    "http://www.w3.org/2001/XMLSchema#string",
    "None",
    "None",
]


class TestTestTest(unittest.TestCase):
    """Tests for `acdh_cidoc_pyutils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_smoke(self):
        self.assertEqual(1, 1)

    def test_002_dates(self):
        for i, x in enumerate(DATE_STRINGS):
            date_literal = date_to_literal(x)
            self.assertEqual(f"{date_literal.datatype}", DATE_TYPES[i])

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
        e52.serialize('e52.ttl')
        self.assertTrue('rdfs:label "1234-05-06"^^xsd:string' in f"{e52.serialize()}")
        e52 = create_e52(uri, begin_of_begin="1222", end_of_end=begin_of_begin)
        e52.serialize('e52.ttl')
        self.assertFalse('rdfs:label "1234-05-06"^^xsd:string' in f"{e52.serialize()}")
        e52.serialize('e521.ttl')

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
                subj, x, type_domain="https://sk.acdh.oeaw.ac.at/types", default_lang="it"
            )
        data = g.serialize(format="turtle")
        g.serialize("appellation.ttl", format="turtle")
        self.assertTrue('rdfs:label "Stahlhelm, Bund der Frontsoldaten"@de' in data)
        self.assertTrue('rdf:value "Stahlhelm, Bund der Frontsoldaten"' in data)
        self.assertTrue("@it" in data)
        self.assertTrue('dfs:label "Gulbransson, Olaf"' in data)
        self.assertTrue('rdfs:label "cosi, maxi"@it' in data)

    def test_008_make_e42_identifiers(self):
        g = Graph()
        doc = ET.fromstring(sample)
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_e42_identifiers(
                subj, x, type_domain="https://sk.acdh.oeaw.ac.at/types", default_lang="it"
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
                set_lang=True,
            )
            data = g.serialize(format="turtle")
            self.assertTrue("@it" in data)
            self.assertTrue("idno/foobarid" in data)
            self.assertTrue("owl:sameAs <https://" in data)
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
                default_prefix=default_prefix
            )
            data = g.serialize(format="turtle")
            self.assertTrue("@it" in data)
            self.assertTrue("idno/foobarid" in data)
            self.assertTrue(default_prefix in data)
            self.assertFalse("owl:sameAs <https://" in data)
            self.assertTrue(match_value in data)
            g.serialize("ids.ttl", format="turtle")

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
        g1, uris = make_occupations(subj, x, id_xpath="@key", not_known_value="ronjaundhanna")
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
            org_label_xpath="./tei:orgName[1]//text()"
        )
        g.serialize("affiliations1.ttl")

    def test_013_make_events(self):
        g = Graph()
        sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0023" sortKey="Bosch_Hieronymus">
        <persName>
            <forename>Hieronymus</forename>
            <surname>Bosch</surname>
        </persName>
        <birth when="1450" type="approx">
            ca. 1450<placeName key="#DWplace00214">’s-Hertogenbosch</placeName></birth>
        <event type="burial">
            <desc>
                <date when="1516-08-08">8. 8. 1516</date>
                <placeName key="#DWplace00162">’s-Hertogenbosch</placeName>
            </desc>
            <note>Burial</note>
        </event>
        <persName type="sk" subtype="pref">Bosch, Hieronymus</persName>
        <occupation type="prim" n="01">Maler</occupation>
        <idno type="GND">11851380X</idno>
        <note type="source" subtype="publ">RKD – Nederlands Instituut voor Kunstgeschiedenis</note>
        <note type="status" subtype="final"/>
    </person>
</TEI>"""
        doc = ET.fromstring(sample)
        for x in doc.xpath(
            ".//tei:place|tei:org|tei:person|tei:bibl", namespaces=NSMAP
        ):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((URIRef("https://foo/bar/types/event/burial"), RDF.type, CIDOC["E55_Type"]))
            g += make_events(
                subj, x, type_domain="https://foo/bar/types", default_lang="en", domain="https://foo/bar/"
            )
        data = g.serialize(format="turtle")
        g.serialize("events.ttl", format="turtle")
        self.assertTrue('rdfs:label "Event: Burial"@en' in data)
        self.assertTrue("@en" in data)
        self.assertTrue('ns1:P82a_begin_of_the_begin "1516-08-08"' in data)
        self.assertTrue('ns1:P82b_end_of_the_end "1516-08-08"' in data)
        self.assertTrue('ns1:P2_has_type <https://foo/bar/types/event/burial>' in data)
        self.assertTrue('ns1:P4_has_time-span <https://foo/bar/dwpers0023/event/0/time-span>' in data)
        self.assertTrue('ns1:P7_took_place_at <https://foo/bar/DWplace00162>' in data)
