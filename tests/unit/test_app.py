"""Endpoint tests for the FastAPI app, exercising the full DTD->RDF round trip.

These hit the real conversion path (lxml DTD parsing + xsltproc + rdflib),
so they require the `xsltproc` binary and the runtime dependencies.
"""
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)

VALID_DTD = "<!ELEMENT note (to,from,heading,body)>\n" \
            "<!ELEMENT to (#PCDATA)>\n" \
            "<!ELEMENT from (#PCDATA)>\n" \
            "<!ELEMENT heading (#PCDATA)>\n" \
            "<!ELEMENT body (#PCDATA)>\n"

VALID_XML = "<?xml version=\"1.0\"?>\n<note><to>Tove</to><from>Jani</from>" \
            "<heading>Reminder</heading><body>Call me</body></note>"

INVALID_DTD = "<!ELEMENT note (to,from"  # truncated / malformed


def test_get_redirects_to_docs():
    resp = client.get("/xml2rdf", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/"


def test_xml2rdf_round_trip_default_turtle():
    resp = client.post("/xml2rdf", json={"xml": VALID_XML, "dtd": VALID_DTD})
    assert resp.status_code == 200
    body = resp.text
    # turtle serialisation of the generated triples should mention our content
    assert "Tove" in body or "Jani" in body


def test_xml2rdf_honours_prefix_without_separator():
    resp = client.post(
        "/xml2rdf",
        json={"xml": VALID_XML, "dtd": VALID_DTD, "prefix": "https://ex.org/ns", "lang": "de"},
    )
    assert resp.status_code == 200
    assert "https://ex.org/ns#" in resp.text


def test_xml2rdf_rejects_invalid_dtd():
    resp = client.post("/xml2rdf", json={"xml": VALID_XML, "dtd": INVALID_DTD})
    assert resp.status_code == 400
    assert "invalid DTD file" in resp.text


def test_dtd2xslt_returns_stylesheet():
    resp = client.post(
        "/dtd2xslt",
        content=VALID_DTD,
        headers={"Content-Type": "application/xml"},
    )
    assert resp.status_code == 200
    assert "xsl:stylesheet" in resp.text


def test_dtd2xslt_rejects_invalid_dtd():
    resp = client.post(
        "/dtd2xslt",
        content=INVALID_DTD,
        headers={"Content-Type": "application/xml"},
    )
    assert "invalid DTD file" in resp.text


# A richer DTD: nested child elements plus CDATA and enumeration attributes,
# exercising the attribute/enumeration and child-loop branches of transform_xml.
RICH_DTD = "<!ELEMENT catalog (item+)>\n" \
           "<!ELEMENT item (#PCDATA)>\n" \
           "<!ATTLIST item id CDATA #REQUIRED kind (book|cd) \"book\">\n"

RICH_XML = "<?xml version=\"1.0\"?>\n<catalog>" \
           "<item id=\"1\" kind=\"book\">Dune</item>" \
           "<item id=\"2\" kind=\"cd\">OK Computer</item></catalog>"


def test_xml2rdf_with_attributes_and_enumeration_turtle():
    resp = client.post("/xml2rdf", json={"xml": RICH_XML, "dtd": RICH_DTD})
    assert resp.status_code == 200
    assert "Dune" in resp.text or "has_id" in resp.text


def test_xml2rdf_accept_rdf_xml():
    resp = client.post(
        "/xml2rdf",
        json={"xml": VALID_XML, "dtd": VALID_DTD},
        headers={"Accept": "application/rdf+xml"},
    )
    assert resp.status_code == 200
    assert "RDF" in resp.text or "rdf" in resp.text


def test_xml2rdf_accept_json_ld():
    resp = client.post(
        "/xml2rdf",
        json={"xml": VALID_XML, "dtd": VALID_DTD},
        headers={"Accept": "application/ld+json"},
    )
    assert resp.status_code == 200
    # json-ld is valid JSON
    assert resp.text.strip().startswith("[") or resp.text.strip().startswith("{")


def test_dtd2xslt_enumeration_stylesheet():
    resp = client.post(
        "/dtd2xslt",
        content=RICH_DTD,
        headers={"Content-Type": "application/xml"},
    )
    assert resp.status_code == 200
    assert "has_id" in resp.text
