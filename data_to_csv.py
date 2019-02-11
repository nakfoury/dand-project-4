#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.ElementTree as ET

import cerberus

from audit import is_postcode, is_street_name, update_postcode, update_street_name
import schema

OSM_PATH = "seattle_washington.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
LOWER_COLON2 = re.compile(r'^([^:]+): ?(.*)$')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, tag_attr_fields=TAGS_FIELDS,
                  way_node_attr_fields=WAY_NODES_FIELDS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for attribute in node_attr_fields:  # shape the node
            if attribute not in element.attrib:
                node_attribs[attribute] = "None"
            else:
                node_attribs[attribute] = element.attrib[attribute]

        for child in element._children:  # shape the node tags
            if child.tag == 'tag':
                if problem_chars.search(child.attrib['k']):  # handles problematic characters
                    break
                tag_attribs = dict.fromkeys(tag_attr_fields)
                tag_attribs['id'] = element.attrib['id']  # get the id from the root element
                key = child.attrib['k']
                colon_pos = child.attrib['k'].find(':')  # handles first colon (if it exists)
                if colon_pos < 0:
                    tag_attribs['key'] = key
                    tag_attribs['type'] = default_tag_type
                else:
                    tag_attribs['key'] = key[:colon_pos]
                    tag_attribs['type'] = key[colon_pos+1:]

                if is_street_name(child):  # update the problematic values, using our audit.py functions
                    tag_attribs['value'] = update_street_name(child.attrib['v'])
                elif is_postcode(child):
                    tag_attribs['value'] = update_postcode(child.attrib['v'])
                else:
                    tag_attribs['value'] = child.attrib['v']
                tags.append(tag_attribs)  # add the iteration tag dict to the tags list
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':  # shape the way
        for attribute in way_attr_fields:
            if attribute not in element.attrib:
                way_attribs[attribute] = "None"
            else:
                way_attribs[attribute] = element.attrib[attribute]

        for i, child in enumerate(element._children):  # shape the way tags
            if child.tag == 'tag':
                if problem_chars.search(child.attrib['k']):  # handles problematic characters
                    continue
                tag_attribs = dict.fromkeys(tag_attr_fields)
                tag_attribs['id'] = element.attrib['id']  # get the id from the root element
                key = child.attrib['k']
                colon_pos = child.attrib['k'].find(':')  # handles first colon (if it exists)
                if colon_pos < 0:
                    tag_attribs['key'] = key
                    tag_attribs['type'] = default_tag_type
                else:
                    tag_attribs['key'] = key[:colon_pos]
                    tag_attribs['type'] = key[colon_pos + 1:]

                if is_street_name(child):  # update the problematic values, using our audit.py functions
                    tag_attribs['value'] = update_street_name(child.attrib['v'])
                elif is_postcode(child):
                    tag_attribs['value'] = update_postcode(child.attrib['v'])
                else:
                    tag_attribs['value'] = child.attrib['v']
                tags.append(tag_attribs)  # add the iteration tag dict to the tags list

            elif child.tag == 'nd':  # shape the way nodes
                way_node_attribs = dict.fromkeys(way_node_attr_fields)
                way_node_attribs['id'] = element.attrib['id']
                way_node_attribs['node_id'] = child.attrib['ref']
                way_node_attribs['position'] = i
                way_nodes.append(way_node_attribs)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Case Study Code: Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Case Study Code: Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Case Study Code: Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Case Study Code: Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
            codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
            codecs.open(WAYS_PATH, 'w') as ways_file, \
            codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
            codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
