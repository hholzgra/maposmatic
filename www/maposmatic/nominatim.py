# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard
# Copyright (C) 2017  Hartmut Holzgraefe

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Nominatim parsing + json export
# Note: we query nominatim in XML format because otherwise we cannot
# access the osm_id tag. Then we format it as json back to the
# javascript routines


"""
Simple API to query http://nominatim.openstreetmap.org

Most of the credits should go to gthe Nominatim team.
"""

from django.utils.translation import gettext
from django.db import connections
import logging
import psycopg2
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree.ElementTree import parse as XMLTree

import ocitysmap
import www.settings

NOMINATIM_BASE_URL = 'http://nominatim.openstreetmap.org'
NOMINATIM_MAX_RESULTS_PER_RESPONSE = 10

NOMINATIM_USER_AGENT = 'MapOSMatic'
if www.settings.ADMINS:
    NOMINATIM_USER_AGENT = '%s (%s)' % (NOMINATIM_USER_AGENT,
                                        www.settings.ADMINS[0][1])

LOG = logging.getLogger('maposmatic')

def reverse_geo(lat, lon):
    """Query the nominatim service for the given lat/long coordinates and
    returns the reverse geocoded informations."""

    request = Request('%s/reverse?%s' %
        (NOMINATIM_BASE_URL, urlencode({'lat': lat, 'lon': lon})))
    request.add_header('User-Agent', NOMINATIM_USER_AGENT)
    f = urlopen(request)

    result = []
    for place in XMLTree(f).getroot().getchildren():
        attribs = dict(place.attrib)
        for elt in place.getchildren():
            attribs[elt.tag] = elt.text
        result.append(attribs)
    return result

def query(query_text, exclude, with_polygons=False, accept_language=None):
    """Query the nominatim service for the given city query and return a
    (python) list of entries for the given squery (eg. "Paris"). Each
    entry is a dictionary key -> value (value is always a
    string). When possible, we also try to uncover the OSM database
    IDs associated with the entries; in that case, an
    "ocitysmap_params" key is provided, which maps to a dictionary
    containing:
      - key "table": when "line" -> refers to table "planet_osm_line";
        when "polygon" -> "planet_osm_polygon"
      - key "id": ID of the OSM database entry
      - key "admin_level": The value stored in the OSM table for admin_level
    """
    xml = _fetch_xml(query_text, exclude, with_polygons, accept_language)
    (hasprev, prevexcludes, hasnext, nextexcludes) = _compute_prev_next_excludes(xml)
    entries = _extract_entries(xml)
    entries = _prepare_and_filter_entries(entries)
    return _canonicalize_data({
        'hasprev'     : hasprev,
        'prevexcludes': prevexcludes,
        'hasnext'     : hasnext,
        'nextexcludes': nextexcludes,
        'entries'     : entries
        })

def _fetch_xml(query_text, exclude, with_polygons, accept_language):
    """Query the nominatim service for the given city query and return a
    XMLTree object."""
    # For some reason, the "xml" nominatim output is ALWAYS used, even
    # though we will later (in views.py) transform this into
    # json. This is because we know that this xml output is correct
    # and complete (at least the "osm_id" field is missing from the
    # json output)

    query_tags = dict(q=query_text.encode("UTF-8"),
                      format='xml', addressdetails=1)

    if with_polygons:
        query_tags['polygon']=1

    if exclude != '':
        query_tags['exclude_place_ids'] = exclude

    request = Request('%s/search/?%s' %
            (NOMINATIM_BASE_URL, urlencode(query_tags)))
    request.add_header('User-Agent', NOMINATIM_USER_AGENT)
    if accept_language:
        request.add_header('Accept-Language', accept_language)

    return XMLTree(urlopen(request))

def _extract_entries(xml):
    """Given a XMLTree object of a Nominatim result, return a (python)
    list of entries for the given squery (eg. "Paris"). Each entry is
    a dictionary key -> value (value is always a string)."""
    result = []
    for place in xml.getroot().getchildren():
        attribs = dict(place.attrib)
        for elt in place.getchildren():
            attribs[elt.tag] = elt.text
        result.append(attribs)

    return result

def _compute_prev_next_excludes(xml):
    """Given a XML response from Nominatim, determines the set of
    "exclude_place_ids" that should be used to get the next set of
    entries and the previous set of entries. We also determine
    booleans saying whether there are or not previous or next entries
    available. This allows the website to show previous/next buttons
    in the administrative boundary search box.

    Args:
         xml (XMLTree): the XML tree of the Nominatim response

    Returns a (hasprev, prevexcludes, hasnext, nextexcludes) tuple,
    where:
         hasprev (boolean): Whether there are or not previous entries.
         prevexcludes (string): String to pass as exclude_place_ids to
            get the previous entries.
         hasnext (boolean): Whether there are or not next entries.
         nextexcludes (string): String to pass as exclude_place_ids to
             get the next entries.
    """
    excludes = xml.getroot().get("exclude_place_ids", None)

    # Assume we always have next entries, because there is no way to
    # know in advance if Nominatim has further entries.
    nextexcludes = excludes
    hasnext = True

    # Compute the exclude list to get the previous list
    prevexcludes = ""
    hasprev = False
    if excludes is not None:
        excludes_list = excludes.split(',')
        hasprev = len(excludes_list) > NOMINATIM_MAX_RESULTS_PER_RESPONSE
        prevexcludes_count = ((len(excludes_list) /
                              NOMINATIM_MAX_RESULTS_PER_RESPONSE) *
                              NOMINATIM_MAX_RESULTS_PER_RESPONSE -
                              2 * NOMINATIM_MAX_RESULTS_PER_RESPONSE)
        if prevexcludes_count >= 0:
            prevexcludes = ','.join(excludes_list[:prevexcludes_count])

    return (hasprev, prevexcludes, hasnext, nextexcludes)

def _canonicalize_data(data):
    """Take a structure containing strings (dict, list, scalars, ...)
    and convert it into the same structure with the proper conversions
    to float or integers, etc."""
    if type(data) is tuple:
        return tuple(_canonicalize_data(x) for x in data)

    if type(data) is list:
        return [_canonicalize_data(x) for x in data]

    if type(data) is dict:
        return dict([(_canonicalize_data(k),
                      _canonicalize_data(v)) for k,v in data.items()])

    if data:
        try:
            return int(data)
        except ValueError:
            try:
                return float(data)
            except ValueError:
                pass

    return data

def _get_admin_boundary_info_from_GIS(cursor, osm_id):
    """Lookup additional data for the administrative boundary of given
    relation osm_id.

    Args:
          osm_id (int) : the OSM id of the relation to lookup

    Returns a tuple (osm_id, admin_level, table_name, valid,
    reason, reason_text).
    """
    # Nominatim returns a field "osm_id" for each result
    # entry. Depending on the type of the entry, it can point to
    # various database entries. For admin boundaries, osm_id is
    # supposed to point to either the 'polygon' or the 'line'
    # table. Usually, the database entry ID in the table is derived by
    # the "relation" items by osm2pgsql, which assigns to that ID the
    # opposite of osm_id... But we still consider that it could be the
    # real osm_id (not its opposite). Let's have fun...
    for table_name in ("polygon", "line"):
        # Lookup the polygon/line table for both osm_id and
        # the opposite of osm_id
        cursor.execute("""select osm_id, admin_level,
                          st_astext(st_envelope(st_transform(way,
                          4002))) AS bbox
                          from planet_osm_%s
                          where osm_id = -%s"""
                       % (table_name,osm_id))
        result = tuple(set(cursor.fetchall()))

        if len(result) == 0:
            continue

        osm_id, admin_level, bboxtxt = result[0]
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bboxtxt)
        (metric_size_lat, metric_size_lon) = bbox.spheric_sizes()
        if (metric_size_lat > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS
            or metric_size_lon > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS):
            valid = False
            reason = "area-too-big"
            reason_text = gettext("Administrative area too big for rendering")
        else:
            valid = True
            reason = ""
            reason_text = ""

        return (osm_id, admin_level, table_name,
                valid, reason, reason_text)

    # Not found
    return None

def _prepare_entry(cursor, entry):
    """Prepare an entry by adding additional informations to it, in the
    form of a ocitysmap_params dictionary.

    Args:
           cursor: database connection cursor
           entry:  the entry to enrich

    Returns nothing, but adds an ocitysmap_params dictionary to the
    entry. It will contain entries 'valid', 'reason', 'reason_text'
    when the entry is invalid, or 'table', 'id', 'valid', 'reason',
    'reason_text' when the entry is valid. Meaning of those values:

           valid (boolean): tells whether the entry is valid for
           rendering or not

           reason (string): non human readable short string that
           describes why the entry is invalid. To be used for
           Javascript comparaison. Empty for valid entries.

           reason_text (string): human readable and translated
           explanation of why the entry is invalid. Empty for valid
           entries.

           table (string): "line" or "polygon", tells in which table
           the administrative boundary has been found. Only present
           for valid entries.

           id (string): the OSM id. Only present for valid entries.

           admin_level (string): the administrative boundary
           level. Only present for valid entries.
    """
    # Try to lookup in the OSM DB, when needed and when it
    # makes sense (ie. the data is coming from a relation)
    entry_type = (entry.get('class'), entry.get('type'), entry.get('osm_type'))
    if entry_type in [('boundary', 'administrative', 'relation'),
                      ('place', 'city', 'relation')]:
        details = _get_admin_boundary_info_from_GIS(cursor, entry["osm_id"])

        if details is None:
            entry["ocitysmap_params"] \
                = dict(valid=False,
                       reason="no-admin",
                       reason_text=gettext("No administrative boundary details from GIS"))
        else:
            (osm_id, admin_level, table_name,
             valid, reason, reason_text) = details
            entry["ocitysmap_params"] \
                = dict(table=table_name, id=osm_id,
                       admin_level=admin_level,
                       valid=valid,
                       reason=reason,
                       reason_text=reason_text)
    else:
        entry["ocitysmap_params"] \
            = dict(valid=False,
                   reason="no-admin",
                   reason_text=gettext("No administrative boundary"))

def _prepare_and_filter_entries(entries):
    """Try to retrieve additional OSM information for the given nominatim
    entries. Among the information, we try to determine the real ID in
    an OSM table for each of these entries. All these additional data
    are stored in the "ocitysmap_params" key of the entry."""

    place_tags = [ 'city', 'town', 'municipality',
                   'village', 'hamlet', 'suburb',
                   'island', 'islet', 'locality',
                   'administrative' ]
    filtered_results = []

    cursor = connections['default'].cursor()
    for entry in entries:

        # Ignore uninteresting tags
        if not entry.get("type") in place_tags:
            continue

        # Our entry wil be part of the result
        filtered_results.append(entry)

        # Enrich the entry with more info
        _prepare_entry(cursor, entry)

    # Some cleanup
    cursor.close()

    return filtered_results

if __name__ == "__main__":
    import pprint, sys
    pp = pprint.PrettyPrinter(indent=4)

    for city in sys.argv[1:]:
        print("###### %s:" % city)
        pp.pprint(query(city))
