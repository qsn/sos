# Copyright (C) 2014 Red Hat, Inc.,
#   Bryn M. Reeves <bmr@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

""" This provides a restricted tag language to define the sosreport
    index/report
"""

try:
    import json
except ImportError:
    import simplejson as json

# PYCOMPAT
from six import iteritems
import six


class Node(object):

    def __str__(self):
        return json.dumps(self.data)

    def can_add(self, node):
        return False


class Leaf(Node):
    """Marker class that can be added to a Section node"""
    pass


class Report(Node):
    """The root element of a report. This is a container for sections."""

    def __init__(self):
        self.data = {}

    def can_add(self, node):
        return isinstance(node, Section)

    def add(self, *nodes):
        for node in nodes:
            if self.can_add(node):
                self.data[node.name] = node.data


class Section(Node):
    """A section is a container for leaf elements. Sections may be nested
    inside of Report objects only."""

    def __init__(self, name):
        self.name = name
        self.data = {}

    def can_add(self, node):
        return isinstance(node, Leaf)

    def add(self, *nodes):
        for node in nodes:
            if self.can_add(node):
                self.data.setdefault(node.ADDS_TO, []).append(node.data)


class Command(Leaf):

    ADDS_TO = "commands"

    def __init__(self, name, return_code, href):
        self.data = {"name": name,
                     "return_code": return_code,
                     "href": href}


class CopiedFile(Leaf):

    ADDS_TO = "copied_files"

    def __init__(self, name, href):
        self.data = {"name": name,
                     "href": href}


class CreatedFile(Leaf):

    ADDS_TO = "created_files"

    def __init__(self, name):
        self.data = {"name": name}


class Alert(Leaf):

    ADDS_TO = "alerts"

    def __init__(self, content):
        self.data = content


class Note(Leaf):

    ADDS_TO = "notes"

    def __init__(self, content):
        self.data = content


class PlainTextReport(object):
    """Will generate a plain text report from a top_level Report object"""

    LEAF = "  * %(name)s"
    ALERT = "  ! %s"
    NOTE = "  * %s"
    DIVIDER = "=" * 72

    subsections = (
        (Command, LEAF,      "-  commands executed:"),
        (CopiedFile, LEAF,   "-  files copied:"),
        (CreatedFile, LEAF,  "-  files created:"),
        (Alert, ALERT,       "-  alerts:"),
        (Note, NOTE,         "-  notes:"),
    )

    buf = []

    def __init__(self, report_node):
        self.report_node = report_node

    def unicode(self):
        self.buf = buf = []
        for section_name, section_contents in sorted(iteritems(
                self.report_node.data)):
            buf.append(section_name + "\n" + self.DIVIDER)
            for type_, format_, header in self.subsections:
                self.process_subsection(section_contents, type_.ADDS_TO,
                                        header, format_)

        # Workaround python.six mishandling of strings ending in '/' by
        # adding a single space following any '\' at end-of-line.
        # See Six issue #60.
        buf = [(val + " ") if val.endswith('\\') else val for val in buf]

        output = u'\n'.join(map(lambda i: (i if isinstance(i, six.text_type)
                                           else six.u(i)), buf))
        if six.PY3:
            return output
        else:
            return output.encode('utf8')

    def process_subsection(self, section, key, header, format_):
        if key in section:
            self.buf.append(header)
            for item in section.get(key):
                self.buf.append(format_ % item)

# vim: set et ts=4 sw=4 :
