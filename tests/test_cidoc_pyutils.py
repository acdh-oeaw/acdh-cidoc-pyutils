import unittest
from lxml.etree import Element
from rdflib import Graph

from acdh_cidoc_pyutils import (
    date_to_literal,
    make_uri,
    create_e52,
    normalize_string,
    extract_begin_end,
)

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
