<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../../templates/master.kid'">

<head>
    <title>rBuilder Log</title>
    <script type="text/javascript">
        function displayTitle() {
            var oldNode = document.getElementById('titleText');
            var newNode = document.createElement("h3");
            var txtNode = document.createTextNode("rBuilder Log");
            newNode.appendChild(txtNode);
            oldNode.parentNode.replaceChild(newNode, oldNode);
        }
    </script>

</head>


<body id="middleWide" onload="displayTitle()">
    <div>
        <p id="titleText">Loading rBuilder Log...</p>
        <textarea readonly="True" rows="20" cols="80" style="width: 100%">${logText}</textarea>
        <form action="rBuilderLog" method="GET">
            <p><button type="submit" class="img"><img src="${tg.url('/static/images/download_button.png')}" alt="Download" /></button></p>
            <br/>
        </form>
    </div>
</body>
</html>
