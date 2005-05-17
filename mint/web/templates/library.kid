<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
    <!-- define the HTML header -->
    <head py:def="html_header(cfg, title, extraScript=None, scriptArgs=None)">
        <title>${title}</title>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}css/common.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/rmint/css/style.css" />
        <script py:if="extraScript">${extraScript(*scriptArgs)}</script>
        <script language="javascript1.2" src="${cfg.staticUrl}apps/rmint/javascript/library.js" /> 
    </head>

    <!-- define the HTML footer -->
    <div class="footer" py:def="html_footer">
        <a py:if="auth.passwordOK" href="login">Log Out (${auth.userId})</a>

        <a py:if="not auth.passwordOK" href="login">Log In</a> | Copyright &#169; 2004-2005 <a href="http://www.rpath.com/">rpath, inc.</a>
    </div>

    <!-- define header image -->
    <div py:def="header_image(cfg)" py:omit="True">
        <h1 class="title">rPath</h1>
    </div>

    <!-- 
        Menu structure:

            [('menu name', 'url', highlighted), ]
    -->
    <div py:def="menu(mainMenu, subMenu=[])" py:omit="1">
        <ul class="menu">
            <li py:for="menuName, menuLink, highlight in mainMenu"
                py:attrs="{'class': highlight and 'highlighted' or False}">
                <a py:if="menuLink" href="${menuLink}">${menuName}</a>
                <span py:if="not menuLink" py:omit="True">${menuName}</span>
            </li>
        </ul>
        <ul class="menu submenu">
            <li py:for="menuName, menuLink, highlight in subMenu"
                py:attrs="{'class': highlight and 'highlighted' or False}">
                <a py:if="menuLink" href="${menuLink}">${menuName}</a>
                <span py:if="not menuLink" py:omit="True">${menuName}</span>
            </li>
        </ul>
   </div>
</html>
