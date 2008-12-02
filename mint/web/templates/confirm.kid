<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Please Confirm')}</title>
    </head>
    <body>
    
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div class="full-content">
                <div class="page-title-no-project">Confirm:</div>
                
                <p class="errormessage">${message}</p>
                <form method="post" action="${yesArgs['func']}">
                <span py:for="k, v in yesArgs.iteritems()">
                    <input type="hidden" name="${k}" value="${v}"/>
                </span>
                <table class="not-wide">
                <tr>
                    <td>
                        <a class="confirmImageButton" href="${noLink}"><img src="${cfg.staticPath}apps/mint/images/no_button.png" alt="No" /></a>
                    </td>
                    <td>
                        <button class="img" id="yes" type="submit">
                            <img src="${cfg.staticPath}apps/mint/images/yes_button.png" alt="Yes" /></button>
                    </td>
                    
                </tr>
                </table>
                </form>
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
