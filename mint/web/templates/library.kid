<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
    <!-- define the HTML header -->
    <head py:def="html_header(title, extraScript=None, scriptArgs=None)">
        <title>${title}</title>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}css/common.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/style.css" />
        <script py:if="extraScript">${extraScript(*scriptArgs)}</script>
        <script language="javascript1.2" src="${cfg.staticUrl}apps/mint/javascript/library.js" /> 
    </head>

    <!-- define the HTML footer -->
    <div class="footer" py:def="html_footer">
        <span py:if="auth.authorized" id="logout">You are logged in as ${auth.username}. <a href="logout">Log Out</a></span>
        <span py:if="not auth.authorized" id="login"><a href="login">Log In</a></span>

        <div id="copyright">Copyright &#169; 2004-2005 <a href="http://www.rpath.com/">rpath, inc.</a></div>
    </div>

    <!-- define header image -->
    <div py:def="header_image()" py:omit="True">
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

    <div py:def="columnTitles(columns = [])" py:omit="1">
            <thead class="results">
                <tr class="results">
                    <td py:for="columnName in columns">${columnName}</td>
                </tr>
            </thead>
    </div>

    <div py:def="resultRow(resultset = [])" py:omit="1">
                    <td class="results"><a href="${resultset[0]}">${resultset[1]}</a></td>
                    <?python
                        resultset.pop(0)
                        resultset.pop(0)
                    ?>
                    <td py:for="item in resultset" class="results">${item}</td>
    </div>

    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
        XXX: add next/prev/skip links
    -->
    <div py:def="searchResults(type, title, results=[])" py:omit="1">
        <?python
            columns = []
            if type == "Projects":
                columns = ('Project Name', 'Project Description', 'Last Modified')
            elif type == "Users":
                columns = ('User Name', 'Full Name', 'E-mail Address', 'Other')
        ?>
        <h2 class="results">${title}</h2>
        <table class="results" width="100%">
            ${columnTitles(columns)}
            <tbody class="results">
                <tr py:for="i, result in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
                    <?python
                        formattedresults = []
                        if type == "Projects":
                            formattedresults = [ 'http://%s' % result[0],
                                result[1], result[2], time.ctime(result[3]) ]
                        elif type == "Users":
                            formattedresults = [ 'userInfo?id=%d' % result[0],
                                result[1], result[2], result[3], result[4] ]
                    ?>
                    ${resultRow(formattedresults)}
                </tr>
            </tbody>
        </table>
    </div>
</html>
