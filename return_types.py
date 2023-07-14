from fastapi import Response


class XSLTResponse(Response):
    media_type = 'application/xslt+xml'


class TurtleResponse(Response):
    media_type = 'text/turtle'


class JsonLdResponse(Response):
    media_type = 'application/ld+json'


class RdfXmlResponse(Response):
    media_type = 'application/rdf+xml'
