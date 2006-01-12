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
      py:extends="'../project.kid', '../library.kid'">
    <td py:def="logo()" id="logo">
        <div>
          <span id="rpath">
            <a href="http://" title="rBuilder main site">
                <img src="${cfg.staticPath}apps/mint/images/corplogo.gif" alt="rPath Logo" height="80" width="80"/>
            </a>
          </span>
          <span id="product">
            <a href="http://" title="rBuilder main site">
                <img src="${cfg.staticPath}apps/mint/images/prodlogo.gif" alt="rBuilder Logo" height="80" width="218"/>
            </a>
          </span>
        </div>
    </td>

    <head py:match="item.tag == 'head'" >
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/generic.js"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/library.js"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/xmlrpc.js"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/basic.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/structure.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/user.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/topNav.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/log.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/contentTypes.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css"/>

        <link rel="shortcut icon" href="http://www.rpath.com/favicon.ico" />
        <link rel="icon" href="http://www.rpath.com/favicon.ico" />
        <div py:replace="item[:]"/>
    </head>
    <body
          py:match="item.tag == 'body'"
          py:attrs="item.attrib">

        <div id="top" align="center">
            <div class="shadowLeft"><div class="shadowRight">
                <div class="surfaceLeft" align="left"><div class="surfaceRight">
                    <table class="noborder" cellspacing="0" cellpadding="0" summary="layout">
                        <tr>
                            ${logo()}
                        </tr>
                    </table>
                </div></div>
            </div></div>
        </div>
        <div id="middle" align="center">
            <div id="crumb">
                <div class="pad">
                </div>
            </div>
        </div>
        <div id="bottom" align="center">
            <div class="shadowLeft"><div class="shadowRight">
                <div class="surfaceLeft" align="left"><div class="surfaceRight">
                    <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                        <tr>
                            <td id="main" class="spanleft" py:replace="item[:]" />
                        </tr>
                    </table>
                </div></div>
            </div></div>
        </div>
        <div id="foot" align="center">
            <div id="copy">
                <div class="pad" style="text-align: center;">
                    <span style="float: left;">Copyright &#169; 2005-2006 rPath, Inc. </span>
                    <span>version ${constants.mintVersion}</span>
                </div>
            </div>
        </div>
    </body>
</html>
