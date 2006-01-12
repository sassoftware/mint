#
# Copyright (c) 2005-2006 rPath, Inc.
# All rights reserved
#

def write(template, **kwargs):
    return template.serialize(output = 'plain', **kwargs)
