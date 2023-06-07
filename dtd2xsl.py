from ontology_generator import get_contents, get_attributes
import xml.etree.ElementTree as Et
from lxml.etree import DTD
import os
from uuid import uuid4


def transform_xml(dtd, xml_file, prefix='https://dtd.org#'):
    root = Et.Element('xsl:stylesheet', attrib={'version': '1.0', 'xmlns:xsl': 'http://www.w3.org/1999/XSL/Transform'})
    Et.SubElement(root, 'xsl:output', attrib={'indent': 'yes'})
    xsl_template_root = Et.SubElement(root, 'xsl:template', attrib={'match': '/'})

    rdf = Et.SubElement(xsl_template_root, 'rdf:RDF', attrib={
        'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xmlns:dtd': prefix})

    for element in dtd.elements():
        name = element.name

        contents = get_contents(element.content)
        attributes = get_attributes(element.attributes())

        element_node = Et.Element('xsl:for-each', attrib={'select': f'//{name}'})
        description = Et.SubElement(element_node, 'rdf:Description', attrib={
            'rdf:about': f'{prefix}{name}-{{generate-id(.)}}'})
        Et.SubElement(description, 'rdf:type', attrib={'rdf:resource': f'{prefix}{name}'})

        for attribute in attributes:
            attribute_check = Et.Element('xsl:if', attrib={'test': f'@{attribute[0]}'})
            attribute_node = Et.SubElement(attribute_check, f'dtd:has_{attribute[0]}')
            Et.SubElement(attribute_node, 'xsl:value-of', attrib={'select': f'@{attribute[0]}'})

            description.append(attribute_check)

        for content in contents:
            if content[0]:
                content_loop = Et.Element('xsl:for-each', attrib={'select': content[0]})
                Et.SubElement(content_loop, f'dtd:has_{content[0]}', attrib={
                    'rdf:resource': f'{prefix}{content[0]}-{{generate-id(.)}}'
                })

                description.append(content_loop)
            else:
                current_content_node = Et.Element('dtd:has_Value')
                Et.SubElement(current_content_node, 'xsl:value-of', attrib={'select': 'current()'})

                description.append(current_content_node)

        rdf.append(element_node)

    tree = Et.ElementTree(root)
    Et.indent(tree)
    tree.write(f'{xml_file}-mapping.xsl', xml_declaration=True, encoding='unicode')

    output = str(uuid4())

    os.system(f'xsltproc -o {output} {xml_file}-mapping.xsl {xml_file}')

    with open(output) as f:
        response = f.read()

    os.remove(output)
    os.remove(f'{xml_file}-mapping.xsl')
    return response


if __name__ == '__main__':
    transform_xml(DTD('gii-norm.dtd'), 'BJNR009650976.xml')
