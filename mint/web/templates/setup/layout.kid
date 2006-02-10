<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
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
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/setup.css" />
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
                    <img src="${cfg.staticPath}/apps/mint/images/corplogo_notrans.png" width="80" height="98" alt="rPath Logo" />
                </div>
                <div id="prodLogo">
                    <img src="${cfg.staticPath}/apps/mint/images/prodlogo.gif" alt="rBuilder Online Logo" />
                </div>
                <div id="topRight">
                </div>
            </div>
            <div class="layout" py:replace="item[:]" />

            <div id="footer">
                <div>
                </div>
                <div id="bottomText" style="border: none;">
                    <span id="copyright">Copyright &copy; 2005-2006 rPath. All Rights Reserved.</span>
                    <span id="tagline">rPath. The Software Appliance Company.</span>
                </div>
            </div>
        </div>
    </body>
</html>
