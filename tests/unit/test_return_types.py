"""The custom Response subclasses only exist to pin specific RDF media types."""
from return_types import (
    JsonLdResponse,
    RdfXmlResponse,
    TurtleResponse,
    XSLTResponse,
)


def test_media_types():
    assert XSLTResponse.media_type == "application/xslt+xml"
    assert TurtleResponse.media_type == "text/turtle"
    assert JsonLdResponse.media_type == "application/ld+json"
    assert RdfXmlResponse.media_type == "application/rdf+xml"
