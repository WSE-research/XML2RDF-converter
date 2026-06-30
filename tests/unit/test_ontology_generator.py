"""Unit tests for the DTD-introspection helpers in ontology_generator.py."""
from io import StringIO

from lxml.etree import DTD

from ontology_generator import get_attributes, get_contents

NOTE_DTD = """<!ELEMENT note (to,from,heading,body)>
<!ELEMENT to (#PCDATA)>
<!ELEMENT from (#PCDATA)>
<!ELEMENT heading (#PCDATA)>
<!ELEMENT body (#PCDATA)>
"""

ATTR_DTD = """<!ELEMENT item (#PCDATA)>
<!ATTLIST item id CDATA #REQUIRED
               kind (a|b) "a">
"""


def _elements(dtd_text):
    return {el.name: el for el in DTD(StringIO(dtd_text)).elements()}


def test_get_contents_returns_child_elements():
    note = _elements(NOTE_DTD)["note"]
    contents = get_contents(note.content)
    names = [c[0] for c in contents]
    assert names == ["to", "from", "heading", "body"]
    # every child element is reported with an occurrence and the 'element' type
    assert all(c[2] == "element" for c in contents)


def test_get_contents_handles_pcdata_leaf():
    body = _elements(NOTE_DTD)["body"]
    contents = get_contents(body.content)
    assert contents == [(None, "once", "pcdata")]


def test_get_contents_returns_empty_for_none():
    assert get_contents(None) == []


def test_get_attributes_empty_when_no_attlist():
    note = _elements(NOTE_DTD)["note"]
    assert get_attributes(note.attributes()) == []


def test_get_attributes_reports_cdata_and_enumeration():
    item = _elements(ATTR_DTD)["item"]
    attrs = {a[0]: a for a in get_attributes(item.attributes())}
    assert attrs["id"][1] == "cdata"
    assert attrs["id"][2] == "required"
    # enumeration attribute carries its declared default value
    assert attrs["kind"][1] == "enumeration"
    assert attrs["kind"][3] == "a"
