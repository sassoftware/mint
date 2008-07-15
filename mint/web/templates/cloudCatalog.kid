<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Cloud Catalog')}</title>
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
                '950', '480', '9.0.28', flashvars, params, attributes);
        </script>
    </head>
    <body>
        <div id="layout">
            <div id="spanleft">
                <div id="cloudCatalog">
                    Cloud Catalog requires the Adobe Flash Player.
                        <a href="http://www.adobe.com/go/getflash/">Get Flash.</a>
                </div>
            </div>
        </div>
    </body>
</html>
