import os
from flask import Flask, request
from dtd2xsl import transform_xml
from lxml.etree import DTD
from io import StringIO, BytesIO
from uuid import uuid4

app = Flask(__name__)


@app.post('/xml2rdf')
def xml2rdf():
    """
    Maps an XML file to RDF while generating the properties from the documents' DTD file

    Requires a JSON payload with the structure
    {
      "xml": "serialized XML file content",
      "dtd": "serialized DTD file content",
      "prefix": "(optional) prefix of the generated properties",
      "lang": "language tag for string constants"
    }

    :return:
    """
    payload = request.json

    try:
        xml = payload['xml']
        dtd = payload['dtd']
    except KeyError:
        return 'missing "xml" or "dtd"', 400

    if 'prefix' in payload:
        prefix = payload['prefix']

        if not prefix.endswith('#') and not prefix.endswith('/'):
            prefix += '#'
    else:
        prefix = 'https://example.org#'

    if 'lang' in payload:
        lang = payload['lang']
    else:
        lang = 'en'

    xml_id = str(uuid4())

    with open(xml_id, 'w') as f:
        f.write(xml)

    try:
        return transform_xml(DTD(StringIO(dtd)), xml_id, prefix, lang)
    finally:
        os.remove(xml_id)


@app.post('/dtd2xslt')
def dtd2xslt():
    dtd = DTD(BytesIO(request.data))

    prefix = request.args.get('prefix', 'https://example.org#')
    lang = request.args.get('lang', 'en')

    if not prefix.endswith('#') and not prefix.endswith('/'):
        prefix += '#'

    return transform_xml(dtd, str(uuid4()), prefix, lang, True)


if __name__ == '__main__':
    app.run()
