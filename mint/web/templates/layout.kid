<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright 2005 rpath, Inc.
# All Rights Reserved
#
from mint import userlevels
from urllib import quote
onload = "javascript:;" 
?>

<html xmlns:py="http://purl.org/kid/ns#"
      py:extends="'project.kid', 'library.kid'">
    <div py:def="breadcrumb()" class="pad" py:strip="True">
    </div>

    <div py:def="rpathProductsMenu" id="browse" class="palette products">
        <h3>rpath products</h3>
        <ul>
            <li><a href="#">Product 1</a></li>
            <li><a href="#">Product 2</a></li>
            <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras erat. Curabitur tempus nulla sit amet justo. Morbi quis tellus sed turpis bibendum egestas. Phasellus nonummy!</li>
        </ul>
    </div>

    <head py:match="item.tag == 'head'" xmlns="http://www.w3.org/1999/xhtml">
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
        <script type="text/javascript" src="${cfg.staticUrl}/apps/mint/javascript/generic.js"/>
        <script type="text/javascript" src="${cfg.staticUrl}/apps/mint/javascript/library.js"/>
        <script type="text/javascript" src="${cfg.staticUrl}/apps/mint/javascript/xmlrpc.js"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/basic.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/structure.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/user.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/topNav.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/log.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/contentTypes.css"/>
        <div py:replace="item[:]"/>
    </head>
    <body xmlns="http://www.w3.org/1999/xhtml"
          py:match="item.tag == 'body'"
          py:attrs="item.attrib"> 
        <?python
            if auth.authorized:
                loginAction = "logout"
            else:
                loginAction = "processLogin"
        ?>
        <div id="top" align="center">
            <div class="shadowLeft"><div class="shadowRight">
                <div class="surfaceLeft" align="left"><div class="surfaceRight">
                    <form method="post" action="${loginAction}">
                        <input py:if="loginAction == 'login'" type="hidden" name="to" value="${quote(toUrl)}" />
                        <table border="0" cellspacing="0" cellpadding="0" summary="layout">
                            <tr>
                                <td id="logo">
                                    <a href="http://${siteHost}/">
                                        <img src="${cfg.staticUrl}/apps/mint/images/logo.gif" alt="rpath logo" width="216" height="72" />
                                    </a>
                                </td>
                                <td id="user" py:if="not auth.authorized">
                                    <div class="pad">
                                        <h4>not logged in | <a href="login">forgot password</a></h4>
                                        <div>
                                            <input type="text" name="username" size="16"/> <label>username</label><br />
                                            <input type="password" name="password" size="16"/> <label>password</label>
                                        </div>
                                    </div>
                                </td>
                                <td id="user" py:if="auth.authorized">
                                    <div class="pad">
                                        <h3>${auth.fullName}</h3>
                                        <h4>${auth.username}</h4>
                                        <div><a href="userSettings" class="arrows">view &#38; edit my account</a></div>

                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td id="topnav">
                                    <div class="pad">
                                        <a href="http://${siteHost}/">Home</a> | 
                                        <a href="#">About rpath</a> |
                                        <a href="#">Contact rpath</a>

                                    </div>
                                </td>
                                <td id="log">
                                    <div class="pad" py:if="not auth.authorized">
                                        <button type="submit" name="submit" value="Log In">Login</button> |
                                        <a href="/register" class="arrows">New Account</a>
                                    </div>
                                    <div class="pad" py:if="auth.authorized">
                                        <button type="submit">Logout</button>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </form>
                </div></div>
            </div></div>
        </div>
        <div id="middle" align="center">
            <div id="crumb">
                <div class="pad">
                    You are here: <a href="http://${siteHost}/">home</a>
                    ${breadcrumb()}
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
                <div class="pad">
                    <span id="botnav">
                        ${legal('http://%s/legal?page=tos' % siteHost, 'Terms of Service')} ${legal('http://%s/legal?page=privacy' % siteHost, 'Privacy Policy')}
                    </span>

                    Copyright &#169; 2005 rpath, Inc.
                </div>
            </div>
        </div>
    </body>
</html>
