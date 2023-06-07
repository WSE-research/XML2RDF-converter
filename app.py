import os
from flask import Flask, request, Response
from dtd2xsl import transform_xml
from lxml.etree import DTD
from io import StringIO
from uuid import uuid4

app = Flask(__name__)


@app.post('/xml2rdf')
def xml2rdf():
    """
    Maps a XML file to RDF while generating the properties from the documents' DTD file

    Requires a JSON payload with the structure
    {
      "xml": "serialized XML file content",
      "dtd": "serialized DTD file content",
      "prefix": "(optional) prefix of the generated properties"
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

        if not prefix.endswith('#'):
            prefix += '#'
    else:
        prefix = 'https://example.org#'

    xml_id = str(uuid4())

    with open(xml_id, 'w') as f:
        f.write(xml)

    response = transform_xml(DTD(StringIO(dtd)), xml_id, prefix)

    os.remove(xml_id)

    return Response(response, content_type='application/rdf+xml')


if __name__ == '__main__':
    app.run()
