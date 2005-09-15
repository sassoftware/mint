<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright 2005 rPath, Inc.
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

    <div py:def="rPathProductsMenu" id="products" class="palette" py:if="False">
        <h3>rPath products</h3>
        <ul>
            <li><a href="#">Product 1</a></li>
            <li><a href="#">Product 2</a></li>
            <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras erat. Curabitur tempus nulla sit amet justo. Morbi quis tellus sed turpis bibendum egestas. Phasellus nonummy!</li>
        </ul>
    </div>

    <head py:match="item.tag == 'head'" xmlns="http://www.w3.org/1999/xhtml">
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
        <script type="text/javascript" src="${cfg.staticPath}/apps/mint/javascript/generic.js"/>
        <script type="text/javascript" src="${cfg.staticPath}/apps/mint/javascript/library.js"/>
        <script type="text/javascript" src="${cfg.staticPath}/apps/mint/javascript/xmlrpc.js"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/basic.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/structure.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/user.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/topNav.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/log.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/contentTypes.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css"/>
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
                    <form method="post" action="http://$siteHost/$loginAction">
                        <input py:if="loginAction == 'login'" type="hidden" name="to" value="${quote(toUrl)}" />
                        <table border="0" cellspacing="0" cellpadding="0" summary="layout">
                            <tr>
                                <td id="logo">
                                </td>
                                <td id="user" py:if="not auth.authorized">
                                    <div class="pad">
                                        <h4>not logged in | <a href="http://$siteHost/login">Forgot Password</a></h4>
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
                                        <div><a href="http://$siteHost/userSettings" class="arrows">view &#38; Edit My Account</a></div>
                                        <div><a href="http://$siteHost/uploadKey" class="arrows">Upload a Package Signing Key</a></div>
                                        <div py:if='auth.admin'><a href="http://$siteHost/administer" class="arrows">Administer</a></div>

                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td id="topnav">
                                    <div class="pad">
                                        <a href="http://${siteHost}/">Home</a> | 
                                        <a py:if="False" href="${cfg.corpSite}">About rPath</a>
                                        <a py:if="False" href="${cfg.corpSite}sales/">Contact rPath</a>
                                        <a href="/help"><b style="color: red;">need help/have feedback?</b></a>
				        <span py:if="cfg.debugMode">
                                            | <span style="color:red;">DEBUG MODE</span>
                                        </span>
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

                    Copyright &#169; 2005 rPath, Inc.
                </div>
            </div>
        </div>
    </body>
</html>
