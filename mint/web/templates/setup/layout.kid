<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint import userlevels
from mint import constants
from urllib import quote
onload = "javascript:;"
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../library.kid'">
    <head py:match="item.tag == '{http://www.w3.org/1999/xhtml}head'" >
        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/setup.css?v=${cacheFakeoutVersion}" />
        <link rel="shortcut icon" href="http://www.rpath.com/favicon.ico" />
        <link rel="icon" href="http://www.rpath.com/favicon.ico" />
        <div py:replace="item[:]"/>
    </head>

    <body py:match="item.tag == '{http://www.w3.org/1999/xhtml}body'"
          py:attrs="item.attrib">
        <div id="main">
            <a name="top" />
            <div id="top">
                <img id="topgradleft" src="${cfg.staticPath}/apps/mint/images/topgrad_left.png" alt="" />
                <img id="topgradright" src="${cfg.staticPath}/apps/mint/images/topgrad_right.png" alt="" />
                <div id="corpLogo">
                    <img src="${cfg.staticPath}/apps/mint/images/corplogo.png" alt="rPath Logo" />
                </div>
                <div id="prodLogo">
                    <img py:if="cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo-rbo.png" alt="rBuilder Online Logo" />
                    <img py:if="not cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo.png" alt="rBuilder Logo" />
                </div>
                <div id="topRight">
                </div>
            </div>
            <div id="page">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/page_topleft.gif" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/page_topright.gif" alt="" />
                <div id="layout" py:replace="item[:]" />
                <div>
                    <div id="footer">
                        <span id="topOfPage"><a href="#top">Top of Page</a></span>
                        <div class="footerLinks">
                            &nbsp;
                        </div>
                        <div id="bottomText">
                            <span id="copyright">Copyright &copy; 2005-2008 rPath. All Rights Reserved.</span>
                        </div>
                    </div><br class="clear" />
                    <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/page_bottomleft.gif" alt="" />
                    <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/page_bottomright.gif" alt="" />
                </div>
                <br />
            </div>
        </div>
    </body>
</html>
