<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:py="http://purl.org/kid/ns#" xmlns="http://www.w3.org/1999/xhtml">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" class="pad">
        You are here: <a href="#">rpath</a>
    </div>

    <td py:def="projectsPane()" id="right" class="projects">
        <div class="pad">
            <h3>My Projects</h3>
            <p py:if="not auth.authorized">
                You must be logged in for your projects to be displayed.
            </p>
            <ul py:if="auth.authorized">
                <li py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="http://${project.getHostname()}/">
                        ${project.getName()}</a><br/>
                        ${userlevels.names[level]}
                </li>
            </ul>
            <ul py:if="auth.authorized">
                <li>
                    <a href="newProject">Create a new project</a>
                </li>
            </ul>
        </div>
    </td>


    <head py:match="item.tag == 'head'">
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
        <title>rpath.com</title>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/basic.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/structure.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/user.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/topNav.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/log.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/contentTypes.css"/>
    </head>
    <body xmlns="http://www.w3.org/1999/xhtml"
          py:match="item.tag == 'body'">
        <div id="top" align="center">
            <div class="shadow">
                <div class="surface" align="left">
                    <form name="login" method="post" action="login2">
                        <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                            <tr>
                                <td id="logo"></td>
                                <td id="user" py:if="not auth.authorized">
                                    <div class="pad">
                                        <h4>not logged in</h4>
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
                                        <div><a href="userSettings" class="arrows">view &amp; edit my account</a></div>

                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td id="topnav">
                                    <div class="pad">
                                        <a href="#">About rpath</a> |
                                        <a href="#">Terms of Service</a> |
                                        <a href="#">Privacy</a> |
                                        <a href="#">Contact rpath</a>
                                    </div>
                                </td>
                                <td id="log"> 
                                    <div class="pad" py:if="not auth.authorized">
                                        <button type="submit" name="submit" value="Log In">Login</button> |
                                        <a href="register" class="arrows">New Account</a>
                                    </div>
                                    <div class="pad" py:if="auth.authorized">
                                        <button type="submit">Logout</button>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </form>
                </div>
            </div>
        </div>
        <div id="middle" align="center">
            <div id="crumb">
                ${breadcrumb()}
            </div>
        </div>
        <div id="bottom" align="center">
            <div class="shadow">
                <div class="surface" align="left">
                    <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                        <tr>
                            <td id="content">
                                <div class="pad">
                                    <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                                        <tr>
                                            <td py:replace="item[:]" />
                                        </tr>
                                    </table>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
        <div id="foot" align="center">
            <div id="copy">
                <div class="pad">
                    Copyright &#169; 2005 rpath.
                </div>
            </div>
        </div>
    </body>
</html>
