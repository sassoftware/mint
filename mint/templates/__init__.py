#
# Copyright (c) 2005-2007 rPath, Inc.
# All rights reserved
#

def write(template, **kwargs):
    return template.serialize(output = 'plain', **kwargs)
