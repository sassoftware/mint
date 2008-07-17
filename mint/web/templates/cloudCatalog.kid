<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'catalogLayout.kid'">
    <head>
        <title>${formatTitle('rBuilder Catalog for EC2(TM)')}</title>
        <script type="text/javascript" src="${cfg.staticPath}/apps/mint/javascript/swfobject.js"></script>
        <script type="text/javascript" src="${cfg.staticPath}/apps/mint/javascript/swf_deeplink_history.js"></script>
        <script type="text/javascript">
            var flashvars = {};
            var params = {
                'menu': false,
                'bgcolor': '#869ca7',
                'allowScriptAccess': 'sameDomain',
                };
            var attributes = {};
            swfobject.embedSWF(staticPath + '/apps/catalog-client/iClouds.swf', 'cloudCatalog',
                '950', '550', '9.0.28', flashvars, params, attributes);
        </script>
    </head>
    <body>
        <div id="layout">
            <div id="cloudCatalog">
                rBuilder Catalog for EC2&trade; requires the Adobe&reg; Flash&reg; Player.
                    <a target="_blank" href="http://www.adobe.com/go/getflash/">Get Adobe&reg; Flash&reg; Player.</a>
            </div>
            <p>
                <a id="learnmore" href="http://wiki.rpath.com/wiki/rBuilder_Online:Catalog_EC2" target="_blank">Read more about the rBuilder Catalog for EC2&trade;</a>
            </p>
        </div>
    </body>
</html>
