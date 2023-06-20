from ontology_generator import get_contents, get_attributes
import xml.etree.ElementTree as Et
from lxml.etree import DTD
import os
from uuid import uuid4
from flask import Response


def transform_xml(dtd: DTD, xml_file: str, prefix: str, lang: str, return_xslt: bool = False):
    root = Et.Element('xsl:stylesheet', attrib={'version': '1.0', 'xmlns:xsl': 'http://www.w3.org/1999/XSL/Transform'})
    Et.SubElement(root, 'xsl:output', attrib={'indent': 'yes'})
    xsl_template_root = Et.SubElement(root, 'xsl:template', attrib={'match': '/'})

    rdf = Et.SubElement(xsl_template_root, 'rdf:RDF', attrib={
        'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xmlns:dtd': prefix,
        'xmlns:rdfs': 'http://www.w3.org/2000/01/rdf-schema#'})

    for element in dtd.elements():
        name = element.name

        contents = get_contents(element.content)
        attributes = get_attributes(element.attributes())

        element_node = Et.Element('xsl:for-each', attrib={'select': f'//{name}'})
        description = Et.SubElement(element_node, 'rdf:Description', attrib={
            'rdf:about': f'{prefix}{name}-{{generate-id(.)}}'})
        Et.SubElement(description, 'rdf:type', attrib={'rdf:resource': f'{prefix}{name}'})

        for attribute in attributes:
            attribute_type = attribute[1]

            attribute_check = Et.Element('xsl:if', attrib={'test': f'@{attribute[0]}'})

            attribute_node = Et.SubElement(attribute_check, f'dtd:has_{attribute[0]}',
                                           attrib={'xml:lang': lang} if attribute_type != 'enumeration' else {})

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

        for content in contents:
            if content[0]:
                content_loop = Et.Element('xsl:for-each', attrib={'select': content[0]})
                Et.SubElement(content_loop, f'dtd:has_{content[0]}', attrib={
                    'rdf:resource': f'{prefix}{content[0]}-{{generate-id(.)}}'
                })

                description.append(content_loop)
            else:
                current_content_node = Et.Element('dtd:has_Value', attrib={'xml:lang': lang})
                Et.SubElement(current_content_node, 'xsl:value-of', attrib={'select': 'current()'})

                description.append(current_content_node)

        rdf.append(element_node)

    tree = Et.ElementTree(root)
    Et.indent(tree)

    output = str(uuid4())

    tree.write(f'{xml_file}-mapping.xsl', xml_declaration=True, encoding='unicode')

    if not return_xslt:
        os.system(f'xsltproc -o {output} {xml_file}-mapping.xsl {xml_file}')

    try:
        if not return_xslt:
            with open(output) as f:
                response = f.read()

            return Response(response, content_type='application/rdf+xml')
        else:
            with open(f'{xml_file}-mapping.xsl') as f:
                return Response(f.read(), content_type='application/xslt+xml')
    finally:
        if not return_xslt:
            os.remove(output)
        os.remove(f'{xml_file}-mapping.xsl')
