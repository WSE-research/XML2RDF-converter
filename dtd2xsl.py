from ontology_generator import get_contents, get_attributes
import xml.etree.ElementTree as Et
from lxml.etree import DTD
import subprocess
import os
from uuid import uuid4
from rdflib import Graph
from return_types import XSLTResponse, RdfXmlResponse, TurtleResponse, JsonLdResponse
from fastapi.responses import PlainTextResponse


def transform_xml(dtd: DTD, xml_file: str, prefix: str, lang: str, output_format: list[str], return_xslt: bool = False):
    root = Et.Element('xsl:stylesheet', attrib={'version': '1.0', 'xmlns:xsl': 'http://www.w3.org/1999/XSL/Transform'})
    Et.SubElement(root, 'xsl:output', attrib={'indent': 'yes'})
    xsl_template_root = Et.SubElement(root, 'xsl:template', attrib={'match': '/'})

    rdf = Et.SubElement(xsl_template_root, 'rdf:RDF', attrib={
        'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xmlns:dtd': prefix,
        'xmlns:rdfs': 'http://www.w3.org/2000/01/rdf-schema#'})

    # Generate all elements
    for element in dtd.elements():
        name = element.name

        # get content (VALUE OR child Elements) of the current element
        contents = get_contents(element.content)

        # get all XML attributes of the current element
        attributes = get_attributes(element.attributes())

        # generate the subject ID for all elements found in a XML file
        element_node = Et.Element('xsl:for-each', attrib={'select': f'//{name}'})
        description = Et.SubElement(element_node, 'rdf:Description')
        description_id_attribute = Et.SubElement(description, 'xsl:attribute', attrib={'name': 'rdf:about'})
        description_id_attribute.text = prefix
        description_id_name = Et.SubElement(description_id_attribute, 'xsl:value-of', attrib={'select': 'local-name()'})
        description_id_name.tail = "-"
        Et.SubElement(description_id_attribute, 'xsl:number', attrib={'level': 'any'})

        # annotate element name as RDF type
        Et.SubElement(description, 'rdf:type', attrib={'rdf:resource': f'{prefix}{name}'})

        # create annotations for all attributes
        for attribute in attributes:
            attribute_type = attribute[1]

            # generate entry only if attribute exists
            attribute_check = Et.Element('xsl:if', attrib={'test': f'@{attribute[0]}'})

            attribute_node = Et.SubElement(attribute_check, f'dtd:has_{attribute[0]}',
                                           attrib={'xml:lang': lang} if attribute_type != 'enumeration' else {})

            # attribute contains only one entry
            if attribute_type != 'enumeration':
                Et.SubElement(attribute_node, 'xsl:value-of', attrib={'select': f'@{attribute[0]}'})
            else:
                enumeration_attr = Et.SubElement(attribute_node, 'xsl:attribute', attrib={'name': 'rdf:resource'})
                enumeration_attr.text = prefix
                Et.SubElement(enumeration_attr, 'xsl:value-of', attrib={'select': f'@{attribute[0]}'})

                attribute_label = Et.Element('rdf:Description')
                attribute_label_select = Et.SubElement(attribute_label, 'xsl:attribute', attrib={'name': 'rdf:about'})
                attribute_label_select.text = prefix
                Et.SubElement(attribute_label_select, 'xsl:value-of', attrib={'select': f'//@{attribute[0]}'})
                attribute_label_rdfs_label = Et.SubElement(attribute_label, 'rdfs:label', attrib={'xml:lang': lang})
                Et.SubElement(attribute_label_rdfs_label, 'xsl:value-of', attrib={'select': f'//@{attribute[0]}'})

                rdf.append(attribute_label)

            description.append(attribute_check)

        # annotate all content
        for content in contents:
            # current content is a child element
            if content[0]:
                content_loop = Et.Element('xsl:for-each', attrib={'select': content[0]})
                rdf_content = Et.SubElement(content_loop, f'dtd:has_{content[0]}')

                rdf_id_attribute = Et.SubElement(rdf_content, 'xsl:attribute', attrib={'name': 'rdf:resource'})
                rdf_id_attribute.text = prefix
                rdf_id_name = Et.SubElement(rdf_id_attribute, 'xsl:value-of', attrib={'select': 'local-name()'})
                rdf_id_name.tail = "-"
                Et.SubElement(rdf_id_attribute, 'xsl:number', attrib={'level': 'any'})

                description.append(content_loop)
            # current content is plain text
            else:
                current_content_node = Et.Element('dtd:has_Value', attrib={'xml:lang': lang})
                Et.SubElement(current_content_node, 'xsl:value-of', attrib={'select': 'current()'})

                description.append(current_content_node)

        rdf.append(element_node)

    tree = Et.ElementTree(root)
    Et.indent(tree)

    output = str(uuid4())

    tree.write(f'{xml_file}-mapping.xsl', xml_declaration=True, encoding='unicode')

    try:
        if not return_xslt:
            status = subprocess.run(['xsltproc', '-o', output, f'{xml_file}-mapping.xsl', xml_file],
                                    capture_output=True)

            if status.returncode != 0:
                return PlainTextResponse(status.stderr, 400)

            g = Graph()
            g.parse(output, format='xml')

            os.remove(output)

            if 'text/turtle' in output_format:
                response = g.serialize()
                return TurtleResponse(content=response)
            elif 'application/rdf+xml' in output_format:
                response = g.serialize(format='xml')
                return RdfXmlResponse(content=response)
            elif 'application/ld+json' in output_format:
                response = g.serialize(format='json-ld')
                return JsonLdResponse(content=response)
            else:
                response = g.serialize()
                return TurtleResponse(content=response)

        else:
            with open(f'{xml_file}-mapping.xsl') as f:
                return XSLTResponse(content=f.read())
    finally:
        os.remove(f'{xml_file}-mapping.xsl')
