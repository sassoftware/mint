#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import elementtree
from elementtree.XMLTreeBuilder import FancyTreeBuilder

from mint.mint_error import *

defaultAllowed = ['b', 'i', 'pre', 'p', 'br', 'a', 'div', 'span']

def checkHTML(data, allowed = defaultAllowed):
    elements = []
    p = FancyTreeBuilder()
    p.end = elements.append

    try:
        p.feed(data)
    except Exception, e:
        raise HtmlParseError(str(e))

    for element in elements:
        if element.tag not in allowed:
            raise HtmlTagNotAllowed(element.tag)
    return True   
