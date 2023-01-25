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
    make_appelations,
    make_ed42_identifiers,
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
        <death when="1958-09-18">18. 9. 1958<placeName key="#DWplace00353"
                >Tegernsee</placeName></death>
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
    </place>
    <place xml:id="DWplace00010">
        <placeName xml:lang="de" type="orig_name">Jaworzno</placeName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/94280/</idno>
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
</TEI>
"""


DATE_STRINGS = ["1900", "-1900", "1900-01", "1901-01-01", "foo"]
DATE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#gYear",
    "http://www.w3.org/2001/XMLSchema#gYear",
    "http://www.w3.org/2001/XMLSchema#gYearMonth",
    "http://www.w3.org/2001/XMLSchema#date",
    "http://www.w3.org/2001/XMLSchema#string",
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
        self.assertTrue(begin, date_string)
        self.assertTrue(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["when"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertTrue(begin, date_string)
        self.assertTrue(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notAfter"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertTrue(begin, date_string)
        self.assertTrue(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notBefore"] = date_string
        begin, end = extract_begin_end(date_object)
        self.assertTrue(begin, date_string)
        self.assertTrue(end, date_string)

        date_string = "1900-12-12"
        date_object = Element("hansi")
        date_object.attrib["notAfter"] = date_string
        date_object.attrib["notBefore"] = "1800"
        begin, end = extract_begin_end(date_object)
        self.assertTrue(begin, "1800")
        self.assertTrue(end, date_string)

    def test_007_make_appelations(self):
        g = Graph()
        doc = ET.fromstring(sample)
        for x in doc.xpath(
            ".//tei:place|tei:org|tei:person|tei:bibl", namespaces=NSMAP
        ):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_appelations(
                subj, x, type_domain="http://hansi/4/ever", default_lang="it"
            )
        data = g.serialize(format="turtle")
        # g.serialize("test.ttl", format="turtle")
        self.assertTrue('rdfs:label "Stahlhelm, Bund der Frontsoldaten"@de' in data)
        self.assertTrue("@it" in data)
        self.assertTrue(
            "P2_has_type <http://hansi/4/ever/person/persname/forename/unused>" in data
        )
        self.assertTrue('dfs:label "Gulbransson, Olaf"' in data)
        self.assertTrue('Leonhard"@bg' in data)
        self.assertTrue("person/persname/forename/unused" in data)

    def test_008_make_ed42_identifiers(self):
        g = Graph()
        doc = ET.fromstring(sample)
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_ed42_identifiers(
                subj, x, type_domain="http://hansi/4/ever", default_lang="it"
            )
            data = g.serialize(format="turtle")
        g = Graph()
        for x in doc.xpath(".//tei:org|tei:place", namespaces=NSMAP):
            xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
            item_id = f"https://foo/bar/{xml_id}"
            subj = URIRef(item_id)
            g.add((subj, RDF.type, CIDOC["hansi"]))
            g += make_ed42_identifiers(
                subj,
                x,
                type_domain="http://hansi/4/ever",
                default_lang="it",
                set_lang=True,
            )
            data = g.serialize(format="turtle")
            self.assertTrue("@it" in data)
            self.assertTrue("idno/foobarid" in data)
            self.assertTrue("owl:sameAs <https://" in data)
            g.serialize("ids.ttl", format="turtle")
