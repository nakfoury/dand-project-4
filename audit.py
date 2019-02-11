import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "seattle_washington.osm"
street_type_re = re.compile(r'(\b\S+\.?)$', re.IGNORECASE)  # matches last word
street_type_re2 = re.compile(r'(\b\S+\.?) \S+$', re.IGNORECASE)  # matches 2nd to last word
directional_re = re.compile(r'((\s[NESW][EW]?)|(\Dth|\Sst))$', re.IGNORECASE)  # matches dxnl at end of st name
postcode_re = re.compile(r'(9\d\d\d\d|\w\d\w ?\d\w\d)')

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Terrace", "Highway", "Alley", "Crescent", "Circle", "Loop"]

street_name_mapping = {"AVE": "Avenue",
                       "Av": "Avenue",
                       "Av.": "Avenue",
                       "Ave": "Avenue",
                       "Ave.": "Avenue",
                       "ave": "Avenue",
                       "AVENUE": "Avenue",
                       "avenue": "Avenue",
                       "Blvd": "Boulevard",
                       "Blvd.": "Boulevard",
                       "boulevard": "Boulevard",
                       "CT": "Court",
                       "Ct": "Court",
                       "Dr": "Drive",
                       "Dr.": "Drive",
                       "DR": "Drive",
                       "Hwy": "Highway",
                       "Ln": "Lane",
                       "LN": "Lane",
                       "PL": "Place",
                       "Pkwy": "Parkway",
                       "Pl": "Place",
                       "RD": "Road",
                       "Rd": "Road",
                       "Rd.": "Road",
                       "ST": "Street",
                       "St": "Street",
                       "St.": "Street",
                       "st": "Street",
                       "street": "Street",
                       "Stree": "Street",
                       "Ter": "Terrace",
                       "WY": "Way",
                       "Wy": "Way"
                       }

directional_mapping = {"North": "N",
                     "South": "S",
                     "East": "E",
                     "West": "W",
                     "Northeast": "NE",
                     "Northwest": "NW",
                     "Southeast": "SE",
                     "Southwest": "SW"}


def audit_street_type(street_types, street_name):
    """Case Study Code + Handling for directionals"""
    d = directional_re.search(street_name)
    if d:
        m = street_type_re2.search(street_name)
    else:
        m = street_type_re.search(street_name)
    if m:
        street_type = m.group(1)
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    """Case Study Code"""
    return (elem.attrib['k'] == "addr:street")


def is_postcode(elem):
    """Return true if tag describes a postcode, or else return false."""
    return (elem.attrib['k'] == "addr:postcode")


def audit(osmfile):
    """Case Study Code"""
    osm_file = open(osmfile, "r")
    unexpected_street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(unexpected_street_types, tag.attrib['v'])
    osm_file.close()
    pprint.pprint(dict(unexpected_street_types))
    return unexpected_street_types


def update_street_name(name):
    """Case Study Code + handling directionals"""
    if directional_re.search(name):
        s = street_type_re2.search(name)
        d = street_type_re.search(name)
    else:
        s = street_type_re.search(name)
        d = None
    if s:
        name.replace(s.group(), street_name_mapping[s.group()])
    if d:
        name.replace(d.group(), directional_mapping[d.group()])
    return name


def update_postcode(postcode):
    """Audit and update Canadian and US postcodes, or return None if postcode is invalid."""
    m = postcode_re.search(postcode)
    if m:
        return m.group(1).replace(' ', '').upper()
    return postcode


audit(OSMFILE)
