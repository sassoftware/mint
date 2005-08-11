<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
                <p class="error">Confirm:</p>
                
                <p class="errormessage">${message}</p>
                <p style="width: 10%;">
                    <a class="option" href="${yesLink}">Yes</a>
                </p>
                <p style="width: 10%;">
                    <a class="option" href="${noLink}">No</a>
                </p>
            </div>
        </td>
    </body>
</html>
