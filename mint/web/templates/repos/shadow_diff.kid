<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mint.helperfuncs import truncateForDisplay, splitVersionForDisplay
?>
    <head>
        <title>${formatTitle('Diff of: %s' % path)}</title>
    </head>
    <body>
        <div id="main">
        <h2 style="text-align: center;">${path}</h2>
        <p py:if="diffinfo" style="text-align: center;" class="help">Below is a side-by-side comparision of ${path} from ${t}=${oldV} and ${t}=${newV}. Lines that are different between the two files are highlighted.</p>
        <p class="help" py:if="not diffinfo">${message}</p>
        <table py:if="diffinfo" style="width: 100%;">
                <tr>
                    <td style="font-weight: bold;"></td>
                    <td style="font-weight: bold; text-align: center;">Parent Version</td>
                    <td style="font-weight: bold;"></td>
                    <td style="font-weight: bold; text-align: center;">Current Version</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Line</td>
                    <td style="font-weight: bold;text-align: center; width: 46%;">${splitVersionForDisplay(str(oldV))}</td>
                    <td style="font-weight: bold;">Line</td>
                    <td style="font-weight: bold; text-align: center; width: 46%;">${splitVersionForDisplay(str(newV))}</td>
                </tr>
                    
            <tr py:for="i in range(len(diffinfo['leftFile']))" style="background: ${i in diffinfo['diffedLines'] and '#c7d7ff' or '#f3f3f3'};">
                <td style="font-weight: ${i in diffinfo['diffedLines'] and 'bold' or 'normal'};">${i in diffinfo['diffedLines']  and '**' or ''}${diffinfo['leftLineNums'][i]}</td>
                <td style="background: ${i in diffinfo['diffedLines'] and '#c7d7ff' or '#E9E9E9'};">${diffinfo['leftFile'][i].replace('  ', '&nbsp;&nbsp;')}</td>
                <td style="font-weight: ${i in diffinfo['diffedLines'] and 'bold' or 'normal'};">${i in diffinfo['diffedLines'] and '**' or ''}${diffinfo['rightLineNums'][i]}</td>
                <td style="background: ${i in diffinfo['diffedLines'] and '#c7d7ff' or '#e9e9e9'};">${diffinfo['rightFile'][i].replace('  ', '&nbsp;&nbsp;')}</td>
            </tr>
        </table>

        <table py:if="not diffinfo" style="width: 100%">
            <tr>
                <th>Contents of ${path}:</th>
            </tr>
            <tr py:for="line in contents">
                <td>${line.replace('  ', '&nbsp;&nbsp;')}</td>
            </tr>
        </table>
        </div>
    </body>
</html>
