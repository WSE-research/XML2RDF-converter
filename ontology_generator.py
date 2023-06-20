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
