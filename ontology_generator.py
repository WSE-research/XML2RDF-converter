import lxml.etree as etree
from rdflib import Graph, URIRef, Namespace, OWL, XSD, RDF, RDFS, Literal
from collections import defaultdict


def get_contents(content):
    contents = []

    if content is None:
        return contents

    if content.name is None and content.type not in ['cdata', 'pcdata']:
        contents += get_contents(content.left)
        contents += get_contents(content.right)
    else:
        contents.append((content.name, content.occur, content.type))

    return contents


def get_attributes(attributes):
    attributes_list = []

    for attribute in attributes:
        attribute_name = attribute.name
        attribute_type = attribute.type
        attribute_default_value = attribute.default_value
        attribute_default = attribute.default
        attribute_prefix = attribute.prefix

        attributes_list.append((attribute_name, attribute_type, attribute_default, attribute_default_value,
                                attribute_prefix))

    return attributes_list


def construct_dtd_rdf(dtd, prefix='https://example.org#'):
    g = Graph()
    namespace = Namespace(prefix)
    g.bind('dtd', namespace)

    domains = defaultdict(list)
    ranges = defaultdict(list)

    for element in dtd.elements():
        name = element.name
        c = element.content

        element_handle = URIRef(f'{prefix}{name}')

        cs = get_contents(c)
        attrs = get_attributes(element.attributes())

        if all((found_element == (None, 'once', 'pcdata')) or (found_element == (None, 'once', 'cdata'))
               for found_element in cs):
            g.add((element_handle, RDF.type, OWL.DatatypeProperty))

            ranges[element_handle].append(XSD.string)
        else:
            g.add((element_handle, RDF.type, OWL.Class))

        for attr_name, attr_type, attr_constraint, attr_default_value, attr_prefix in attrs:
            attr_handle = URIRef(f'{element_handle}_{attr_name}')
            g.add((attr_handle, RDF.type, OWL.DatatypeProperty))
            g.add((attr_handle, RDFS.domain, element_handle))

            if attr_type in ['cdata', 'pcdata']:
                g.add((attr_handle, RDFS.range, XSD.string))

            if attr_constraint == 'implied':
                g.add((attr_handle, OWL.minCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))
            elif attr_constraint == 'required':
                g.add((attr_handle, OWL.cardinality, Literal(0, datatype=XSD.nonNegativeInteger)))
            elif attr_constraint == 'fixed':
                g.add((attr_handle, OWL.hasValue, Literal(attr_default_value, datatype=XSD.string)))

        for content_name, content_card, content_element in cs:
            if content_name is None:
                continue

            object_property = URIRef(f'{prefix}has_{content_name}')

            g.add((object_property, RDF.type, OWL.ObjectProperty))

            domains[object_property].append(element_handle)
            ranges[object_property].append(URIRef(f'{prefix}{content_name}'))

    for key in domains:
        domain_class = URIRef(f'{key}_Domain')

        g.add((domain_class, RDF.type, OWL.Class))
        g.add((URIRef(key), RDFS.domain, domain_class))

        for domain in domains[key]:
            for domain_type in g.query(f'SELECT ?type WHERE {{<{domain}> a ?type .}}'):
                if domain_type[0] == OWL.Class:
                    g.add((domain, RDFS.subClassOf, domain_class))
                else:
                    g.add((domain, RDFS.subPropertyOf, domain_class))

    for key in ranges:
        range_class = URIRef(f'{key}_Range')

        g.add((range_class, RDF.type, OWL.Class))
        g.add((URIRef(key), RDFS.range, range_class))

        for rangeEntry in ranges[key]:
            for range_type in g.query(f'SELECT ?type WHERE {{<{rangeEntry}> a ?type .}}'):
                if range_type[0] == OWL.Class:
                    g.add((rangeEntry, RDFS.subClassOf, range_class))
                else:
                    g.add((rangeEntry, RDFS.subPropertyOf, range_class))

    res = g.query('SELECT ?domain ?prop WHERE { ?domain_prop rdfs:range ?range . ?prop rdfs:subClassOf ?range . '
                  '?prop a owl:DatatypeProperty . ?domain_prop rdfs:domain ?dom . ?dom owl:oneOf ?domain . }')

    domains = defaultdict(list)

    for domain, subject in res:
        domains[subject].append(domain)

    for key in domains:
        prop_domain = URIRef(f'{key}_Property_Domain')

        g.add((URIRef(key), RDFS.domain, prop_domain))
        g.add((prop_domain, RDF.type, OWL.Class))

        for domain in domains[key]:
            for domain_type in g.query(f'SELECT ?type WHERE {{<{domain}> a ?type . }}'):
                if domain_type[0] == OWL.Class:
                    g.add((domain, RDFS.subClassOf, prop_domain))
                else:
                    g.add((domain, RDFS.subPropertyOf, prop_domain))

    g.serialize('ontology.ttl')


if __name__ == '__main__':
    construct_dtd_rdf(etree.DTD('gii-norm.dtd'))
