<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head>
        <title>rpath.org: please confirm</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
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
        </td>
    </body>
</html>
