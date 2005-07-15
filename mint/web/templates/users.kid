<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from mint import userlisting
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("User Listing")}
    <body>
        ${header_image()}
        <div py:def="formatResults(resultset = [])" py:omit="True">
            <?python
                formattedresults = [ 'http://%s' % resultset[0],
                    resultset[1], resultset[2],
                    time.ctime(resultset[3]), time.ctime(resultset[4]),
                    resultset[5] ]
            ?>
            ${resultRow(formattedresults)}
        </div>

        <div py:def="sortOrderForm(sortOrder = 0)" py:omit="True">
            <form method="get" action="users">
                <select name="sortOrder">
                    <option py:for="key, value in userlisting.orderhtml.items()"
                        value="${key}" py:attrs="{'selected': (key==sortOrder) and 'selected' or None}"
                        py:content="value" />
                </select>
                <input type="submit" name="submit" value="Go" />
            </form>
        </div>

        <div id="content">
${navigation("projects?sortOrder=%d"%(sortOrder), count, limit, offset)}
            <table class="results">
${columnTitles(('User Name', 'Name', 'Time Created', 'Time Last Accessed', 'About'))}
${searchResults(results)}
            </table>
            ${html_footer()}
        </div>
    </body>
</html>
