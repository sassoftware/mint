<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("Search Results")}
    <body>
        ${header_image()}
        <!--
        ${menu([("Edit Project Description", None, True)])}
        -->
        <div id="content">
            ${searchResults( "Results for " + search, ("Project Name", "Project Description", "Last Modified"), results)}

            ${html_footer()}
        </div>
    </body>
</html>
