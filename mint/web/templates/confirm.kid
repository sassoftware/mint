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
            <p class="error">Confirm:</p>

            <p class="errormessage">${message}</p>
            <table>
                <tr><td>
                    <p style="width: 50%;">
                        <a class="option" href="${noLink}">No</a>
                    </p>
                </td>
                <td>
                    <p style="width: 50%;">
                        <a class="option" href="${yesLink}">Yes</a>
                    </p>
                </td><td width="50%"/></tr>
            </table>
        </div>
    </body>
</html>
