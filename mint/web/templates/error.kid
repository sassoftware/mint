<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    ${html_header(shortError)}
    <body>
        ${header_image()}

        <div id="content">
            <h2>${shortError}</h2>

            <p class="error">Error: ${error}</p>
            <p>
                Please go back and try again or contact 
                <a href="mailto:custom@specifix.com">custom@specifix.com</a> or join the IRC channel
                <b>#conary</b> on the <a href="http://www.freenode.net/">FreeNode</a> IRC network
                for assistance.
            </p>

            ${html_footer()}
        </div>
    </body>
</html>
