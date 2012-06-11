#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import restbase
from mint_test import mint_rephelp

from mint import buildtypes
from mint.rest import errors

class ReleasesTest(restbase.BaseRestTest):

    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupReleases()

    def testDeleteRelease(self):
        client = self.getRestClient(admin=True, username='adminuser')
        req, results = client.call('GET', 'products/testproject/releases')
        releaseId = results.releases[-1].releaseId
        uri = 'products/testproject/releases/%s' % releaseId
        req, results = client.call('DELETE', uri)
        assert(results)
        self.assertRaises(errors.ReleaseNotFound, client.call,'GET', uri)

    def testLatestRelease(self):
        db = self.openMintDatabase()
        client = self.getRestClient(admin=True, username='adminuser')
        uri = 'products/testproject/releases?limit=1'
        req, results = client.call('GET', uri)
        releases = results.releases
        assert(len(releases) == 1)
        assert(releases[0].releaseId == 2)
        assert(releases[0].timePublished)
        db.publishRelease(self.productShortName, 1, True)
        req, results = client.call('GET', uri)
        releases = results.releases
        assert(len(releases) == 1)
        assert(releases[0].releaseId == 1)
        assert(releases[0].timePublished)


    def testImagesShowPublished(self):
        client = self.getRestClient(admin=True, username='adminuser')
        uri = 'products/testproject/releases?limit=1'
        req, results = client.call('GET', uri)
        releases = results.releases
        assert(len(releases) == 1)
        assert(releases[0].releaseId == 2)
        assert(releases[0].timePublished)
        req, results = client.call('GET', 'products/testproject/releases/2/images')
        assert(results.images[0].published)
        assert(results.images[0].released)

    def testAddImageToRelease(self):
        db = self.openMintDatabase()
        imageId = self.createImage(db, self.productShortName,
                                   buildtypes.TARBALL,
                                   name = 'Image 3')
        self.setImageFiles(db, self.productShortName, imageId)
        db.commit()

        client = self.getRestClient(admin=True, username='adminuser')
        uri = 'products/testproject/releases?limit=1'
        req, results = client.call('POST',
                'products/testproject/releases/1/images',
                body="<image><imageId>%s</imageId></image>" % imageId)
        assert(results.imageId == imageId)
        assert(results.released == True)
        assert(results.published == False)



testsetup.main()
