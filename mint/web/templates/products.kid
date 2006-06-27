<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Products: %s' % project.getNameForDisplay())}</title>
        <link py:if="products" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Products" href="${basePath}rss" />
    </head>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER or auth.admin
    ?>
    <div py:strip="True" py:def="productTableRow(productName, product, isOwner, isFirst, numProductsInVersion, defaultHidden, hiddenName)">
        <?python
            from mint import producttypes
            from mint.helperfuncs import truncateForDisplay
            files = product.getFiles()
            rowAttrs = defaultHidden and { 'name': hiddenName, 'style': 'display: none;' } or {}
        ?>
        <tr py:attrs="rowAttrs">
            <td py:if="isFirst" rowspan="${numProductsInVersion}">
                ${truncateForDisplay(product.getName(), maxWordLen=25)}<br />
                <span style="color: #999">${truncateForDisplay(productName, maxWordLen=30)}</span>
            </td>
            <td>
                    <a href="product?id=${product.getId()}">${product.getArch()} ${producttypes.typeNamesShort[product.productType]}</a>
            </td>
            <td py:if="product.getPublished()">
                <div py:strip="True" py:for="i, file in enumerate(files)">
                    <?py fileUrl = cfg.basePath + "downloadImage/" + str(file['fileId']) + "/" + file['filename'] ?>
                    <a py:attrs="downloadTracker(cfg, fileUrl)" href="http://${cfg.siteHost}${fileUrl}">
                        ${file['title'] and file['title'] or "Disc " + str(i+1)}
                    </a> (${file['size']/1048576}&nbsp;MB)<br />
                </div>
                <span py:if="not files">N/A</span>
            </td>
            <div py:strip="True" py:if="isOwner and not product.getPublished()">
            <td><a onclick="javascript:deleteProduct(${product.getId()});" href="#" class="option">Delete</a> 
            </td>
            <td><a py:if="product.getFiles()" onclick="javascript:setProductPublished(${product.getId()});" class="option" href="#">Publish</a>
            </td>
            </div>
        </tr>
    </div>

     <div py:strip="True" py:def="productsTable(products, productVersions, isOwner, wantPublished, numShowByDefault)">
        <?python
            ithProduct = 0
            filteredProducts = [x for x in products if x.getPublished() == wantPublished]
            hiddenName = 'older_product_' + (wantPublished and 'p' or 'u')
        ?>
        <table border="0" cellspacing="0" cellpadding="0" class="productstable">
            <tr py:if="filteredProducts">
                <th>Name</th>
                <th>Built For</th>
                <th colspan="2" py:if="isOwner and not wantPublished">&nbsp;</th>
                <div py:strip="True" py:if="wantPublished">
                    <th>Downloads</th>
                </div>
            </tr>
        <div py:strip="True" py:for="productName, productsForVersion in productVersions">
            <?python
                filteredProductsForVersion = [ x for x in productsForVersion if x.getPublished() == wantPublished ]
                isFirst = True
                lastProductName = ""
                hideByDefault = (ithProduct >= numShowByDefault)
            ?>
            <div py:strip="True" py:if="filteredProductsForVersion" rowspan="${len(filteredProductsForVersion)}">
                <div py:strip="True" py:for="product in filteredProductsForVersion">
                    ${productTableRow(productName, product, isOwner, (lastProductName != productName), len(filteredProductsForVersion), hideByDefault, hiddenName)}
                    <?python lastProductName = productName ?>
                </div>
            </div>
            <?python
                if filteredProductsForVersion:
                    ithProduct += 1
            ?>
        </div>
        </table>
        <p py:if="not filteredProducts">This project has no ${wantPublished and "published" or "unpublished"} products.</p>
        <p py:if="ithProduct > numShowByDefault"><a name="${hiddenName}" onclick="javascript:toggle_display_by_name('${hiddenName}');" href="#">(show all ${wantPublished and "published" or "unpublished"} products)</a></p>
        <p py:if="isOwner and wantPublished"><strong><a href="newProduct">Create a new product</a></strong></p>
    </div>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${productsMenu(publishedProducts, isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <?python hasVMwareImage = True in [ x.hasVMwareImage() for x in publishedProducts ] ?>
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2><a py:if="hasVMwareImage" title="Download VMware Player" href="http://www.vmware.com/download/player/"><img class="vmwarebutton" src="${cfg.staticPath}apps/mint/images/get_vmware_player.gif" alt="Download VMware Player" /></a>Products</h2>
                <h3 py:if="isOwner">Published Products</h3>
                ${productsTable(products, productVersions, isOwner, True, 5)}

                <div py:if="isOwner">
                    <h3>Unpublished Products</h3>
                    ${productsTable(products, productVersions, isOwner, False, 5)}
                </div>
            </div>
        </div>
    </body>
</html>
