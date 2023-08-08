import os
from fastapi import FastAPI, Body, Header
from fastapi.responses import RedirectResponse, PlainTextResponse
from dtd2xsl import transform_xml
from lxml.etree import DTD, DTDParseError
from io import StringIO
from uuid import uuid4
from pydantic import BaseModel
from typing import Annotated
import uvicorn
from return_types import XSLTResponse, TurtleResponse

app = FastAPI(title='XML to RDF converter using XML DTD files', root_path='/xml-to-rdf', docs_url='/',
              description='This web service provides an endpoint to convert a XML file to RDF. The structure of'
                          'the XML file has to be provided with an additional DTD file. Although, you can generate'
                          'a XSLT file from the DTD file. You can use it to transform any XML document that'
                          'is valid against the DTD file.')


class XML2RDFBody(BaseModel):
    xml: str
    dtd: str
    lang: str | None = None
    prefix: str | None = None


@app.get('/xml2rdf', include_in_schema=False)
def redirect_to_api_documentation():
    return RedirectResponse('/')


@app.post('/xml2rdf', responses={
    200: {
        "content": {
            "text/turtle": {},
            "application/rdf+xml": {},
            "application/ld+json": {}
        },
        "description": "RDF triples generated from the provided XML file using its DTD"
    }
}, description='Endpoint used to transform a XML file to RDF. The relationship of all elements is build using the DTD '
               'of the XML file', response_class=TurtleResponse)
def xml2rdf(payload: XML2RDFBody, accept: Annotated[list[str] | None, Header()] = None):
    """
    Maps an XML file to RDF while generating the properties from the documents' DTD file

    Requires a JSON payload with the structure
    {
      "xml": "serialized XML file content",
      "dtd": "serialized DTD file content",
      "prefix": "(optional) prefix of the generated properties",
      "lang": "language tag for string constants"
    }

    :return: RDF/XML representation of the provided data
    """
    xml = payload.xml
    dtd = payload.dtd

    if payload.prefix:
        prefix = payload.prefix

        if not prefix.endswith('#') and not prefix.endswith('/'):
            prefix += '#'
    else:
        prefix = 'https://example.org#'

    if payload.lang:
        lang = payload.lang
    else:
        lang = 'en'

    xml_id = str(uuid4())

    with open(xml_id, 'w') as f:
        f.write(xml)

    try:
        return transform_xml(DTD(StringIO(dtd)), xml_id, prefix, lang, accept)
    except DTDParseError:
        return PlainTextResponse("invalid DTD file", 400)
    finally:
        os.remove(xml_id)


@app.post('/dtd2xslt', responses={
    200: {
        "content": {
            "application/xslt+xml": {}
        },
        "description": "XSLT file used to transform XML to RDF/XML data"
    }
}, description='Endpoint returning the XSLT file usable to transform a XML file to RDF/XML. The translation rules '
               'are inferred from a DTD file.', response_class=XSLTResponse)
def dtd2xslt(dtd_content: Annotated[str, Body(media_type='application/xml')],
             prefix: str | None = 'https://example.org#', lang: str | None = 'en',
             accept: Annotated[list[str] | None, Header()] = None):
    """
    Generate an XML stylesheet from a DTD file

    URI arguments:

    prefix: base URI for the triples defined in the stylesheet

    lang: language tag for string literals

    :return: XSLT data usable for mapping an XML file to RDF/XML
    """
    try:
        dtd = DTD(StringIO(dtd_content))

        if not prefix.endswith('#') and not prefix.endswith('/'):
            prefix += '#'

        return transform_xml(dtd, str(uuid4()), prefix, lang, accept, True)
    except DTDParseError:
        return PlainTextResponse('invalid DTD file')


if __name__ == '__main__':
    uvicorn.run('app:app')
