#!/usr/bin/python
import os
import sys

maybeRoot = os.path.dirname(os.path.dirname(__file__))
if os.path.exists(os.path.join(maybeRoot, 'mint', 'lib')):
    sys.path.insert(maybeRoot)

from mint.scripts import some_module
sys.exit(some_module.Script().run())
