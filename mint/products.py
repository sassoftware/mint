#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

import sys
import time
import urlparse

from mint import database
from mint import jobs
from mint import producttypes
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
from mint.mint_error import MintError, ParameterError
from mint.producttemplates import dataHeadings, dataTemplates

from conary import versions
from conary.deps import deps

class TroveNotSet(MintError):
    def __str__(self):
        return "this product needs a be associated with a group or fileset trove."

class ProductMissing(MintError):
    def __str__(self):
        return "the requested product does not exist."

class ProductDataNameError(MintError):
    def __str__(self):
        return self.str

    def __init__(self, reason = None):
        if reason is None:
            self.str = "Named value is not in data template."
        else:
            self.str = reason

class ProductsTable(database.KeyedTable):
    name = "Products"
    key  = "productId"

    createSQL = """
                CREATE TABLE Products (
                    productId            %(PRIMARYKEY)s,
                    projectId            INTEGER NOT NULL,
                    pubReleaseId         INTEGER,
                    productType          INTEGER,
                    name                 VARCHAR(255),
                    description          TEXT,
                    troveName            VARCHAR(128),
                    troveVersion         VARCHAR(255),
                    troveFlavor          VARCHAR(4096),
                    troveLastChanged     INTEGER,
                    timeCreated          DOUBLE,
                    createdBy            INTEGER,
                    timeUpdated          DOUBLE,
                    updatedBy            INTEGER
                )"""

    fields = ['productId', 'projectId', 'pubReleaseId', 
              'productType', 'name', 'description',
              'troveName', 'troveVersion', 'troveFlavor', 'troveLastChanged',
              'timeCreated', 'createdBy', 'timeUpdated', 'updatedBy']

    indexes = {"ProductProjectIdIdx":\
                 """CREATE INDEX ProductProjectIdIdx
                        ON Products(projectId)""",
               "ProductPubReleaseIdIdx":\
                 """CREATE INDEX ProductPubReleaseIdIdx
                        ON Products(pubReleaseId)"""}


    def new(self, **kwargs):
        projectId = kwargs['projectId']
        cu = self.db.cursor()
        cu.execute("""SELECT productId FROM Products
                          WHERE projectId=?
                          AND troveLastChanged IS NULL""", projectId)
        for productId in [x[0] for x in cu.fetchall()]:
            cu.execute("DELETE FROM ProductData WHERE productId=?", productId)
        cu.execute("""DELETE FROM Products
                        WHERE projectId=?
                        AND troveLastChanged IS NULL""", projectId)
        self.db.commit()
        return database.KeyedTable.new(self, **kwargs)

    def iterProductsForProject(self, projectId):
        """ Returns an iterator over the all of the productIds in a given
            project with ID projectId. The iterator is ordered by the date
            the associated group grove last changed in descending order
            (most to lease recent)."""

        cu = self.db.cursor()

        cu.execute("""SELECT productId FROM Products
                      WHERE projectId=? AND
                            troveName IS NOT NULL AND
                            troveVersion IS NOT NULL AND
                            troveFlavor IS NOT NULL AND
                            troveLastChanged IS NOT NULL
                            ORDER BY troveLastChanged DESC, productId""",
                   projectId)

        for results in cu.fetchall():
            yield int(results[0])

    def setTrove(self, productId, troveName, troveVersion, troveFlavor):
        cu = self.db.cursor()
        cu.execute("""UPDATE Products SET troveName=?,
                                          troveVersion=?,
                                          troveFlavor=?,
                                          troveLastChanged=?
                      WHERE productId=?""",
                   troveName, troveVersion,
                   troveFlavor, time.time(),
                   productId)
        self.db.commit()
        return 0

    def getTrove(self, productId):
        cu = self.db.cursor()

        cu.execute("""SELECT troveName,
                             troveVersion,
                             troveFlavor
                      FROM Products
                      WHERE productId=?""",
                   productId)
        r = cu.fetchone()

        name, version, flavor = r[0], r[1], r[2]
        if not flavor:
            flavor = "none"
        if not name or not version:
            raise TroveNotSet
        else:
            return name, version, flavor

    def getPublished(self, productId):
        cu = self.db.cursor()

        cu.execute("SELECT IFNULL((SELECT pubReleaseId FROM Products WHERE productId=?), 0)", productId)
        return bool(cu.fetchone()[0])

    def deleteProduct(self, productId):
        cu = self.db.transaction()
        try:
            r = cu.execute("DELETE FROM Products WHERE productId=?", productId)
            r = cu.execute("DELETE FROM ProductData WHERE productId=?", productId)
            r = cu.execute("DELETE FROM Jobs WHERE productId=?", productId)
            r = cu.execute("DELETE FROM ProductFiles WHERE productId=?", productId)
        except:
            self.db.rollback()
        else:
            self.db.commit()

    def productExists(self, productId):
        cu = self.db.cursor()

        cu.execute("SELECT count(*) FROM Products WHERE productId=?", productId)
        return cu.fetchone()[0]

class Product(database.TableObject):
    __slots__ = ProductsTable.fields

    def __eq__(self, val):
        for item in [x for x in self.__slots__ if x not in \
                     ('productId', 'troveLastChanged', 'timeCreated')]:
            if self.__getattribute__(item) != val.__getattribute__(item):
                return False
        return self.getDataDict() == val.getDataDict()

    def getItem(self, id):
        return self.server.getProduct(id)

    def getId(self):
        return self.productId

    def getName(self):
        return self.name

    def setName(self, name):
        return self.server.setProductName(self.productId, name.strip())

    def getDefaultName(self):
        """ Returns a generated product name based on the group trove
            the product is based upon and its version. This should be
            as a default name if the user doesn't supply one in the UI."""
        return "%s=%s" % (self.getTroveName(),
                self.getTroveVersion().trailingRevision().asString())

    def getDesc(self):
        return self.description

    def setDesc(self, desc):
        return self.server.setProductDesc(self.productId, desc.strip())

    def getProjectId(self):
        return self.projectId

    def getUserId(self):
        return self.userId

    def getTrove(self):
        return tuple(self.server.getProductTrove(self.productId))

    def getTroveName(self):
        return self.troveName

    def getTroveVersion(self):
        return versions.ThawVersion(self.troveVersion)

    def getTroveFlavor(self):
        return deps.ThawFlavor(self.troveFlavor)

    def getChangedTime(self):
        return self.troveLastChanged

    def setTrove(self, troveName, troveVersion, troveFlavor):
        self.server.setProductTrove(self.productId,
            troveName, troveVersion, troveFlavor)
        self.refresh()

    def setProductType(self, productType):
        assert(productType in producttypes.TYPES)
        self.productType = productType
        return self.server.setProductType(self.productId, productType)

    def getProductType(self):
        if not self.productType:
            self.productType = self.server.getProductType(self.productId)
        return self.productType

    def getJob(self):
        jobId = self.server.getJobIdForProduct(self.id)
        if jobId:
            return jobs.Job(self.server, jobId)
        else:
            return None

    def getFiles(self):
        return self.server.getProductFilenames(self.productId)

    def setFiles(self, filenames):
        return self.server.setProductFilenames(self.productId, filenames)

    def getArch(self):
        flavor = deps.ThawFlavor(self.getTrove()[2])
        if flavor.members:
            return flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        else:
            return "none"

    def setPublished(self, pubReleaseId, published):
        return self.server.setProductPublished(self.productId,
                pubReleaseId, published)

    def getPublished(self):
        return self.pubReleaseId

    def getDataTemplate(self):
        if self.productType:
            return dataTemplates[self.productType]
        else:
            return {}

    def getDisplayTemplates(self):
        return [(x, dataHeadings[x], dataTemplates[x]) \
                for x in dataTemplates.keys()]
        # FIXME: use the following code once we revert to new product model
        if self.productType:
            return [(dataHeadings[self.productType], \
                     dataTemplates[self.productType])]
        else:
            return 'No Image Selected', {}

    def setDataValue(self, name, value, dataType = None, validate = True):
        template = self.getDataTemplate()
        if (name not in template and validate) or (dataType is None and not validate):
            raise ProductDataNameError("Named value not in data template: %s" %name)
        if dataType is None:
            dataType = template[name][0]
        if dataType == RDT_ENUM and value not in template[name][3].values():
            raise ParameterError("%s is not a legal enumerated value" % value)
        return self.server.setProductDataValue(self.getId(), name, value, dataType)

    def getDataValue(self, name):
        template = self.getDataTemplate()
        isPresent, val = self.server.getProductDataValue(self.getId(), name)
        if not isPresent and name not in template:
            raise ProductDataNameError( "%s not in data template" % name)
        if not isPresent:
            val = template[name][1]
        return val

    def getDataDict(self):
        dataDict = self.server.getProductDataDict(self.getId())
        template = self.getDataTemplate()
        for name in list(template):
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict

    def deleteProduct(self):
        return self.server.deleteProduct(self.getId())

    def hasVMwareImage(self):
        """ Returns True if product has a VMware player image. """
        filelist = self.getFiles()
        for file in filelist:
            if file["filename"].endswith(".vmware.zip"):
                return True
        return False

