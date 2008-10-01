<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
from mint.web.templatesupport import projectText
?>

    <head>
        <title>${formatTitle('Group Builder: %s' % project.getNameForDisplay())}</title>
        <script type="text/javascript">
            <![CDATA[
                addLoadEvent(function() {getCookStatus('${jobId}')});
            ]]>
        </script>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>

                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">Cooking Your Group</div>
                    
                    <h2>Group Builder: ${curGroupTrove.recipeName}</h2>
           
                    <p>Your request to cook ${curGroupTrove.recipeName} has been
                    submitted.</p>
    
                    ${statusArea("Cook")}
    
                    <p>When the job status "Finished" appears, your group
                    has finished cooking. Click on the "Manage Images" link in the
                    "${projectText().title()} Resources" sidebar, and select
                    ${curGroupTrove.recipeName} to create an image.</p>
                </div>
                <br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
