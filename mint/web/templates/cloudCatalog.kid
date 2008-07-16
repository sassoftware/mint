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
        <script py:if="hasCredentials" type="text/javascript">
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
            <div py:if="hasCredentials" id="cloudCatalog">
                rBuilder Catalog for EC2&trade; requires the Adobe&reg; Flash&reg; Player.
                    <a href="http://www.adobe.com/go/getflash/">Get Adobe&reg; Flash&reg; Player.</a>
            </div>
            <div py:if="not hasCredentials" style="width: 100%; height: 400px; text-align: center">
                 <h1>Before You Begin...</h1>
                 <p>rBuilder Catalog for EC2&trade; requires that your user account has valid
                    credentials for Amazon Web Services&trade;.</p>
                <p>Please <a href="http://${SITE}cloudSettings">click here to setup your credentials</a>.</p>
                <p>Alternatively, you may <a href="http://${SITE}">return to ${cfg.productName}</a>.</p>
            </div>
        </div>
    </body>
</html>
