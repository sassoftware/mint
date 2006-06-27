#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import time

from mint import producttypes
from mint import jobstatus
from mint.cmdline import commands

from conary import versions
from conary.lib import options, log
from conary.conaryclient.cmdline import parseTroveSpec


def waitForProduct(client, productId, interval = 5):
    product = client.getProduct(productId)
    job = product.getJob()

    while job.status in (jobstatus.WAITING, jobstatus.RUNNING):
        time.sleep(interval)
        job.refresh()

    log.info("Job ended with '%s' status: %s" % (jobstatus.statusNames[job.status], job.statusMessage))


class ProductCreateCommand(commands.RBuilderCommand):
    commands = ['product-create']
    paramHelp = "<project name> <troveSpec> <image type>"

    docs = {'wait' : 'wait until a product job finishes'}

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM

    def runCommand(self, client, cfg, argSet, args):
        wait = argSet.pop('wait', False)
        args = args[1:]
        if len(args) < 3:
            return self.usage()

        projectName, troveSpec, productType = args
        project = client.getProjectByHostname(projectName)
        product = client.newProduct(project.id, project.name)

        n, v, f = parseTroveSpec(troveSpec)
        assert(n and v and f is not None)
        v = versions.VersionFromString(v)
        v.resetTimeStamps(0)
        product.setTrove(n, v.freeze(), f.freeze())

        assert(productType.upper() in producttypes.validProductTypes)
        product.setProductType(producttypes.validProductTypes[productType.upper()])

        job = client.startImageJob(product.id)
        log.info("Product %d job started (job id %d)." % (product.id, job.id))
        if wait:
            waitForProduct(client, product.id)
        return product.id
commands.register(ProductCreateCommand)


class ProductWaitCommand(commands.RBuilderCommand):
    commands = ['product-wait']
    paramHelp = "<product id>"

    def runCommand(self, client, cfg, argSet, args):
        args = args[1:]
        if len(args) < 1:
            return self.usage()

        productId = int(args[0])
        waitForProduct(client, productId)
commands.register(ProductWaitCommand)
