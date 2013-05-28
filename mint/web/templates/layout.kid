<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint import maintenance
from mint import helperfuncs
from mint.web.templatesupport import projectText

from urllib import quote
onload = "javascript:;"
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    <head py:match="item.tag == '{http://www.w3.org/1999/xhtml}head'" >
        <meta name="KEYWORDS" content="rPath, rBuilder, rBuilder Online, rManager, rPath Linux, rPl, Conary, Software Appliance, Application image, Software as a Service, SaaS, Virtualization, virtualisation, open source, Linux," />
        <meta name="DESCRIPTION" content="rPath enables applications to be delivered as a software appliance which combines a software application and a streamlined version of system software that easily installs on industry standard hardware (typically a Linux server)." />

        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/library.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/rpc.js?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/help.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/search.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/tables.css?v=${cacheFakeoutVersion}" />

        <link rel="shortcut icon" href="${cfg.staticPath}apps/mint/images/favicon.ico" />
        <link rel="icon" href="${cfg.staticPath}apps/mint/images/favicon.ico" />
        <div py:replace="item[:]"/>
    </head>

    <body py:match="item.tag == '{http://www.w3.org/1999/xhtml}body'"
          py:attrs="item.attrib">
        <div py:if="bulletin" id="bulletin">${XML(bulletin)}</div>
        <a name="top" />
        <div id="main">
            <div id="top">
                <img id="topgradleft" src="${cfg.staticPath}/apps/mint/images/topgrad_left.png" alt="" />
                <img id="topgradright" src="${cfg.staticPath}/apps/mint/images/topgrad_right.png" alt="" />
                <div id="corpLogo">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/corplogo.png" alt="rPath Logo" />
                    </a>
                </div>
                <div id="prodLogo">
                    <a href="http://${SITE}">
                        <img py:if="cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo-rbo.png" alt="rBuilder Online Logo" />
                        <img py:if="not cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo.png" alt="rBuilder Logo" />
                    </a>
                </div>
            </div>
            <div py:if="maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE" id="maintmode">
                <p>${cfg.productName} is currently in maintenance mode.
                <a py:if="auth.admin" href="${cfg.basePath}admin/maintenance">Click here to enter the site administration menu.</a>
                </p>
            </div>
            <?python
                if 'errors' in locals():
                    errorMsgList = errors
            ?>
            <div py:if="infoMsg" id="info" class="status" py:content="infoMsg" />
            <div py:if="errorMsgList" id="errors" class="status"><strong>The following ${(len(errorMsgList) == 1) and "error" or "errors"} occurred:</strong>
                <p py:for="e in errorMsgList" py:content="e" />
            </div>
            <div id="page">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/page_topleft.gif" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/page_topright.gif" alt="" />
                <div id="layout" py:replace="item[:]" />
                ${layoutFooter()}<br />
            </div>
        </div>
    </body>
</html>
