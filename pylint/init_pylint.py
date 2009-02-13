#
# Copyright (c) 2008 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

import os
import sys
sys.path.insert(0, os.environ['CONARY_PATH'])
#sys.path.insert(0, os.environ['RMAKE_PATH'])
sys.path.insert(0, os.environ['PRODUCT_DEFINITION_PATH'])
sys.path.insert(0, os.environ['CATALOG_SERVICE_PATH'])
sys.path.insert(0, os.environ['PACKAGE_CREATOR_SERVICE_PATH'])
sys.path.insert(0, os.environ['MINT_PATH'])
sys.path.insert(0, os.environ['MCP_PATH'])
sys.path.insert(0, os.environ['XOBJ_PATH'])
sys.path.insert(0, os.environ['RESTLIB_PATH'])
