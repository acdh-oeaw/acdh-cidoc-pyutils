[![flake8 Lint](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/lint.yml/badge.svg)](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/lint.yml)
[![Test](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/test.yml/badge.svg)](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/acdh-oeaw/acdh-cidoc-pyutils/branch/main/graph/badge.svg?token=XRF7ANN1TM)](https://codecov.io/gh/acdh-oeaw/acdh-cidoc-pyutils)
[![PyPI version](https://badge.fury.io/py/acdh-cidoc-pyutils.svg)](https://badge.fury.io/py/acdh-cidoc-pyutils)

# acdh-cidoc-pyutils
Helper functions for the generation of CIDOC CRMish RDF (from XML/TEI data)

## Installation

* install via `pip install acdh-cidoc-pyutils`

## Examples

* For 'real-world-examples' see e.g. [semantic-kraus project](https://github.com/semantic-kraus/lk-data/blob/main/scripts/make_rdf.py)
* also take a look into [test_cidoc_pyutils.py](https://github.com/acdh-oeaw/acdh-cidoc-pyutils/blob/main/tests/test_cidoc_pyutils.py)

### extract `cidoc:P14i_performed FRBROO:F51_ Pursuit` triples from `tei:person/tei:occupation` nodes
```python
import lxml.etree as ET
from rdflib import URIRef
rom acdh_cidoc_pyutils import make_occupations, NSMAP
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
g, uris = make_occupations(subj, x, "https://foo.bar", id_xpath="@key")
print(g.serialize())
# returns
```
```ttl
@prefix ns1: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://foo/bar/DWpers0091> ns1:P14i_performed <https://foo/bar/DWpers0091/occupation/3>,
        <https://foo/bar/DWpers0091/occupation/franzi>,
        <https://foo/bar/DWpers0091/occupation/hansi>,
        <https://foo/bar/DWpers0091/occupation/sumsi> .

<https://foo/bar/DWpers0091/occupation/3> a <http://iflastandards.info/ns/fr/frbr/frbroo#F51> ;
    rdfs:label "Bäckerin"@de .

<https://foo/bar/DWpers0091/occupation/franzi> a <http://iflastandards.info/ns/fr/frbr/frbroo#F51> ;
    rdfs:label "Sängerin"@de .

<https://foo/bar/DWpers0091/occupation/hansi> a <http://iflastandards.info/ns/fr/frbr/frbroo#F51> ;
    rdfs:label "Bürgermeister"@it ;
    ns1:P4_has_time-span <https://foo/bar/DWpers0091/occupation/hansi/time-span> .

<https://foo/bar/DWpers0091/occupation/hansi/time-span> a ns1:E52_Time-Span ;
    rdfs:label "1900-12 - 2000"^^xsd:string ;
    ns1:P82a_begin_of_the_begin "1900-12"^^xsd:gYearMonth ;
    ns1:P82b_end_of_the_end "2000"^^xsd:gYear .

<https://foo/bar/DWpers0091/occupation/sumsi> a <http://iflastandards.info/ns/fr/frbr/frbroo#F51> ;
    rdfs:label "Tischlermeister/Fleischhauer"@de ;
    ns1:P4_has_time-span <https://foo/bar/DWpers0091/occupation/sumsi/time-span> .

<https://foo/bar/DWpers0091/occupation/sumsi/time-span> a ns1:E52_Time-Span ;
    rdfs:label "1233-02-03 - 1233-02-03"^^xsd:string ;
    ns1:P82a_begin_of_the_begin "1233-02-03"^^xsd:date ;
    ns1:P82b_end_of_the_end "1233-02-03"^^xsd:date .
```

### extract birth/death triples from `tei:person`

```python
import lxml.etree as ET
from rdflib import URIRef
from acdh_cidoc_pyutils import make_birth_death_entities, NSMAP

sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <person xml:id="DWpers0091" sortKey="Gulbransson_Olaf_Leonhard">
        <persName type="pref">Gulbransson, Olaf</persName>
        <birth when="1873-05-26">
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

doc = ET.fromstring(sample)
x = doc.xpath(".//tei:person[1]", namespaces=NSMAP)[0]
xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
item_id = f"https://foo/bar/{xml_id}"
subj = URIRef(item_id)
event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
    subj, x, place_id_xpath="//tei:placeName[1]/@key
)
event_graph, birth_uri, birth_timestamp = make_birth_death_entities(
    subj, x, event_type="death", verbose=True, date_node_xpath="/tei:date[1]",
    place_id_xpath="//tei:settlement[1]/@key"
)
event_graph.serialize(format="turtle")
# returns
```
```ttl
@prefix ns1: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# birth example

<https://foo/bar/dwpers0091/birth> a ns1:E67_Birth ;
    rdfs:label "Geburt von Gulbransson, Olaf Leonhard"@fr ;
    ns1:P4_has_time-span <https://foo/bar/dwpers0091/birth/time-span> ;
    ns1:P7_took_place_at <https://foo/bar/DWplace00139> ;
    ns1:P98_brought_into_life <https://foo/bar/dwpers0091> .

<https://foo/bar/dwpers0091/birth/time-span> a ns1:E52_Time-Span ;
    rdfs:label "1873-05-26 - 1873-05-26"^^xsd:string ;
    ns1:P82a_begin_of_the_begin "1873-05-26"^^xsd:date ;
    ns1:P82b_end_of_the_end "1873-05-26"^^xsd:date .

# death example

<https://foo/bar/dwpers0091/death> a ns1:E69_Death ;
    rdfs:label "Geburt von Gulbransson, Olaf Leonhard"@fr ;
    ns1:P100_was_death_of <https://foo/bar/dwpers0091> ;
    ns1:P7_took_place_at <https://foo/bar/pmb50>
    ns1:P4_has_time-span <https://foo/bar/dwpers0091/death/time-span> .

<https://foo/bar/dwpers0091/death/time-span> a ns1:E52_Time-Span ;
    rdfs:label "1905-07-04 - 2000"^^xsd:string ;
    ns1:P82a_begin_of_the_begin "1905-07-04"^^xsd:date ;
    ns1:P82b_end_of_the_end "2000"^^xsd:gYear .
```


### create `ns1:P168_place_is_defined_by "Point(456 123)"^^<geo:wktLiteral> .` from tei:coords
```python
import lxml.etree as ET
from rdflib import Graph, URIRef, RDF
from acdh_cidoc_pyutils import coordinates_to_p168, NSMAP, CIDOC
sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <place xml:id="DWplace00092">
        <placeName type="orig_name">Reval (Tallinn)</placeName>
        <location><geo>123 456</geo></location>
    </place>
</TEI>"""

doc = ET.fromstring(sample)
g = Graph()
for x in doc.xpath(".//tei:place", namespaces=NSMAP):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"https://foo/bar/{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E53_Place"]))
    g += coordinates_to_p168(subj, x)
print(g.serialize())
# returns
```
```ttl
...
    ns1:P168_place_is_defined_by "Point(456 123)"^^<geo:wktLiteral> .
...
```
* Function parameter `verbose` prints information in case the given xpath does not return expected results which is a text node with two numbers separated by a given separator (default value is `separator=" "`)
* Function parameter `inverse` (default: `inverse=False`) changes the order of the coordinates.



### date-like-string to casted rdflib.Literal

```python
from acdh_cidoc_pyutils import date_to_literal d
dates = [
    "1900",
    "1900-01",
    "1901-01-01",
    "foo",
]
for x in dates:
    date_literal = date_to_literal(x)
    print((date_literal.datatype))

# returns
# http://www.w3.org/2001/XMLSchema#gYear
# http://www.w3.org/2001/XMLSchema#gYearMonth
# http://www.w3.org/2001/XMLSchema#date
# http://www.w3.org/2001/XMLSchema#string
```

### make some random URI

```python
from acdh_cidoc_pyutils import make_uri

domain = "https://hansi4ever.com/"
version = "1"
prefix = "sumsi"
uri = make_uri(domain=domain, version=version, prefix=prefix)
print(uri)
# https://hansi4ever.com/1/sumsi/6ead32b8-9713-11ed-8065-65787314013c

uri = make_uri(domain=domain)
print(uri)
# https://hansi4ever.com/8b912e66-9713-11ed-8065-65787314013c
```

### create an E52_Time-Span graph

```python
from acdh_cidoc_pyutils import create_e52, make_uri
uri = make_uri()
e52 = create_e52(uri, begin_of_begin="1800-12-12", end_of_end="1900-01")
print(e52.serialize())
# returns
```
```ttl
# @prefix ns1: <http://www.cidoc-crm.org/cidoc-crm/> .
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# <https://hansi4ever.com/387fb457-971b-11ed-8065-65787314013c> a ns1:E52_Time-Span ;
#     rdfs:label "1800-12-12 - 1900-01"^^xsd:string ;
#     ns1:P82a_begin_of_the_begin "1800-12-12"^^xsd:date ;
#     ns1:P82b_end_of_the_end "1900-01"^^xsd:gYearMonth .
```
### creates E42 from tei:org|place|person

takes a tei:person|place|org node, extracts their `@xml:id` and all `tei:idno` elements, derives `idoc:E42_Identifier` triples and relates them to a passed in subject via `cidoc:P1_is_identified_by`

```python
import lxml.etree as ET
from rdflib import Graph, URIRef, RDF
from acdh_cidoc_pyutils import make_e42_identifiers, NSMAP, CIDOC
sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <place xml:id="DWplace00092">
        <placeName type="orig_name">Reval (Tallinn)</placeName>
        <placeName xml:lang="de" type="simple_name">Reval</placeName>
        <placeName xml:lang="und" type="alt_label">Tallinn</placeName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/42085/</idno>
        <idno type="URI" subtype="geonames">https://www.geonames.org/588409</idno>
        <idno subtype="foobarid">12345</idno>
    </place>
</TEI>"""

doc = ET.fromstring(sample)
g = Graph()
for x in doc.xpath(".//tei:place|tei:org|tei:person|tei:bibl", namespaces=NSMAP):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"https://foo/bar/{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E53_Place"]))
    g += make_e42_identifiers(
        subj, x, type_domain="http://hansi/4/ever", default_lang="it",
    )
print(g.serialize(format="turtle"))
# returns
```
```ttl
@prefix ns1: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://foo/bar/dwplace00092> a ns1:E53_Place ;
    ns1:P1_is_identified_by <https://foo/bar/dwplace00092/identifier/DWplace00092>,
        <https://foo/bar/dwplace00092/identifier/idno/0>,
        <https://foo/bar/dwplace00092/identifier/idno/1>,
        <https://foo/bar/dwplace00092/identifier/idno/2> ;
    owl:sameAs <https://pmb.acdh.oeaw.ac.at/entity/42085/>,
        <https://www.geonames.org/588409> .

<http://hansi/4/ever/idno/URI/geonames> a ns1:E55_Type .

<http://hansi/4/ever/idno/foobarid> a ns1:E55_Type .

<http://hansi/4/ever/idno/pmb> a ns1:E55_Type .

<http://hansi/4/ever/xml-id> a ns1:E55_Type .

<https://foo/bar/dwplace00092/identifier/DWplace00092> a ns1:E42_Identifier ;
    rdfs:label "Identifier: DWplace00092"@it ;
    rdf:value "DWplace00092";
    ns1:P2_has_type <http://hansi/4/ever/xml-id> .

<https://foo/bar/dwplace00092/identifier/idno/0> a ns1:E42_Identifier ;
    rdfs:label "Identifier: https://pmb.acdh.oeaw.ac.at/entity/42085/"@it ;
    rdf:value "https://pmb.acdh.oeaw.ac.at/entity/42085/";
    ns1:P2_has_type <http://hansi/4/ever/idno/pmb> .

<https://foo/bar/dwplace00092/identifier/idno/1> a ns1:E42_Identifier ;
    rdfs:label "Identifier: https://www.geonames.org/588409"@it ;
    rdf:value "https://www.geonames.org/588409" 
    ns1:P2_has_type <http://hansi/4/ever/idno/URI/geonames> .

<https://foo/bar/dwplace00092/identifier/idno/2> a ns1:E42_Identifier ;
    rdfs:label "Identifier: 12345"@it ;
    rdf:value "12345";
    ns1:P2_has_type <http://hansi/4/ever/idno/foobarid> .
```

### creates appellations from tei:org|place|person

takes a tei:person|place|org node, extracts `persName, placeName and orgName` texts, `@xml:lang` and custom type values and returns `cidoc:E33_41` and `cidoc:E55` nodes linked via `cidoc:P1_is_identified_by` and `cidoc:P2_has_type`

```python
import lxml.etree as ET
from rdflib import Graph, URIRef, RDF
from acdh_cidoc_pyutils import make_appellations, NSMAP, CIDOC

sample = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <place xml:id="DWplace00092">
        <placeName type="orig_name">Reval (Tallinn)</placeName>
        <placeName xml:lang="de" type="simple_name">Reval</placeName>
        <placeName xml:lang="und" type="alt_label">Tallinn</placeName>
        <idno type="pmb">https://pmb.acdh.oeaw.ac.at/entity/42085/</idno>
    </place>
</TEI>"""

doc = ET.fromstring(sample)
g = Graph()
for x in doc.xpath(".//tei:place|tei:org|tei:person|tei:bibl", namespaces=NSMAP):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"https://foo/bar/{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E53_Place"]))
    g += make_appellations(
        subj, x, type_domain="http://hansi/4/ever", default_lang="it"
    )

g.serialize(format="ttl")
# returns
```
```ttl
@prefix ns1: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://foo/bar/dwplace00092> a ns1:E53_Place ;
    ns1:P1_is_identified_by <https://foo/bar/dwplace00092/appellation/0>,
        <https://foo/bar/dwplace00092/appellation/1>,
        <https://foo/bar/dwplace00092/appellation/2> .

<http://hansi/4/ever/alt-label> a ns1:E55_Type ;
    rdfs:label "alt_label" .

<http://hansi/4/ever/orig-name> a ns1:E55_Type ;
    rdfs:label "orig_name" .

<http://hansi/4/ever/simple-name> a ns1:E55_Type ;
    rdfs:label "simple_name" .

<https://foo/bar/dwplace00092/appellation/0> a ns1:E33_E41_Linguistic_Appellation ;
    rdfs:label "Reval (Tallinn)"@it ;
    ns1:P2_has_type <http://hansi/4/ever/orig-name> .

<https://foo/bar/dwplace00092/appellation/1> a ns1:E33_E41_Linguistic_Appellation ;
    rdfs:label "Reval"@de ;
    ns1:P2_has_type <http://hansi/4/ever/simple-name> .

<https://foo/bar/dwplace00092/appellation/2> a ns1:E33_E41_Linguistic_Appellation ;
    rdfs:label "Tallinn"@und ;
    ns1:P2_has_type <http://hansi/4/ever/alt-label> .
```
### normalize_string

```python
from acdh_cidoc_pyutils import normalize_string
string = """\n\nhallo
mein schatz ich liebe    dich
    du bist         die einzige für mich
        """
print(normalize_string(string))
# returns
# hallo mein schatz ich liebe dich du bist die einzige für mich
```

### extract date attributes (begin, end)

expects typical TEI date attributes like `@when, @when-iso, @notBefore, @notAfter, @from, @to, ...` and returns a tuple containg start- and enddate values. If only `@when or @when-iso` or only `@notBefore or @notAfter` are provided, the returned values are the same, unless the default parameter `fill_missing` is set to `False`. 

```python
from lxml.etree import Element
from acdh_cidoc_pyutils import extract_begin_end

date_string = "1900-12-12"
date_object = Element("{http://www.tei-c.org/ns/1.0}tei")
date_object.attrib["when-iso"] = date_string
print(extract_begin_end(date_object))

# returns
# ('1900-12-12', '1900-12-12')

date_string = "1900-12-12"
date_object = Element("{http://www.tei-c.org/ns/1.0}tei")
date_object.attrib["when-iso"] = date_string
print(extract_begin_end(date_object, fill_missing=False))

# returns
# ('1900-12-12', None)

date_object = Element("{http://www.tei-c.org/ns/1.0}tei")
date_object.attrib["notAfter"] = "1900-12-12"
date_object.attrib["notBefore"] = "1800"
print(extract_begin_end(date_object))

# returns
# ('1800', '1900-12-12')
```

## development

* `pip install -r requirements_dev.txt`
* `flake8` -> linting
* `coveage run -m pytest` -> runs tests and creates coverage stats