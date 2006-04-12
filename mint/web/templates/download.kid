<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Project Release')}</title>
        <meta http-equiv="refresh" content="2;url=${url}" />
    </head>
    <body>
        <div class="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div id="spanleft">
                <h1>Download File</h1>
                <p>Your file will begin downloading shortly.</p>

                <p>If it does not, click here to download: <a href="${url}">${url}</a></p>
            </div>
        </div>
    </body>
</html>
