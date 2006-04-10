<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Please Confirm')}</title>
    </head>
    <body>
        <div class="layout">
            <h2>Confirm:</h2>

            <p class="errormessage">${message}</p>
            <table>
                <tr><td>
                    <p style="width: 50%;">
                        <a href="${noLink}"><img src="${cfg.staticPath}apps/mint/images/no_button.png" alt="No" /></a>
                    </p>
                </td>
                <td>
                    <form method="post" action="${yesArgs['func']}">
                        
                        <span py:for="k, v in yesArgs.iteritems()">
                          <input type="hidden" name="${k}" value="${v}"/>
                        </span>
                        <p style="width: 50%;">
                        <button class="img" id="yes" type="submit"><img src="${cfg.staticPath}apps/mint/images/yes_button.png" alt="Yes" /></button>
                    </p>
                    </form>
                </td><td width="50%"/></tr>
            </table>
        </div>
    </body>
</html>
