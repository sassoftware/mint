<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    ${html_header("Search Results")}
    <body>
        ${header_image()}
        <div id="content">
            ${searchResults(type, "Results for " + terms, count, results, modified, limit, offset)}

            ${html_footer()}
        </div>
    </body>
</html>
