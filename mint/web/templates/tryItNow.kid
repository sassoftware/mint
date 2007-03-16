<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle("Try It Now!")}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/ec2.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript">
            <![CDATA[
                addLoadEvent(function() { launcher = new EC2Launcher(${blessedAMIId}); });
            ]]>
        </script>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

                <h1>Try It Now</h1>
                <h2>Feel the face-rocking power of EC2!</h2>
                <h3>${shortDescription}</h3>

                <p py:if="buildId">This <acronym title="Amazon Machine Image">AMI</acronym> was built using ${cfg.productName} (<a href="${basePath}build?id=${buildId}">more info</a>).</p>

                <p>${helptext}</p>

                <button id="startButton">Launch It!</button>

        </div>
    </body>
</html>
