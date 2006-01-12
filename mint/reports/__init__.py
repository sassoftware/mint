#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
"""
Mint Report Application

@group Base Reporting Hooks: reports
@group Report Modules: new_users
"""
import os

global _reportlab_present
try:
    import reportlab
    _reportlab_present = True
except NameError:
    _reportlab_present = False

from reports import MintReport

def moduleHasReportObject(repModule):
    for objName in repModule.__dict__.keys():
        try:
            if MintReport in repModule.__dict__[objName].__bases__:
                return True
        except AttributeError:
            pass
    return False

global availableReports
if _reportlab_present:
    moduleNames = [''.join(x.split('.py')) for x in
                        os.listdir(__path__[0])
                        if x.endswith('.py') and not x.startswith('#')
                        and not x.startswith('.') and not x.startswith('_')
                        and x != 'reports.py']
    __dict__ = {}
    availableReports = []
    for moduleName in moduleNames:
        mintModule = __import__('mint.reports', {}, {}, [moduleName])
        targetModule = mintModule.__dict__[moduleName]
        if moduleHasReportObject(targetModule):
            __dict__[moduleName] = targetModule
            availableReports.append(moduleName)
else:
    availableReports = []

def getAvailableReports():
    return availableReports
