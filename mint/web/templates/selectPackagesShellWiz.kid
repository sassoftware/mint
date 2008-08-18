<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid', 'packagecreator.kid', 'wizard.kid'">
<?python
from mint.helperfuncs import formatProductVersion, truncateForDisplay
import string
?>
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Create Package: %s' % project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${wizard_navigation()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>${project.getNameForDisplay(maxWordLen = 50)} - Version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</h1>
            <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/packagelist.js?v=${cacheFakeoutVersion}" />
            <h2>Select Additional Packages</h2>
            <div id="jumpto_box"><span><label for="jumpto">Type a filter term: </label><input name="jumpto" id="jumpto_box" value="" disabled="disabled"/><input id="jumpto_box_clear" type="image" src="${cfg.staticPath}apps/mint/images/clear_filter.gif" title="Clear Filter"/></span></div>
            <div id="filter_selections" style="display:none"/>
            <div style="display:none" id="filter_navigation_link_template"></div>
            <form name="selectPackagesForm" method="post" action="processSelectPackages">
            <div class="packageList">
                <div class="packageList_navigation">
                  <div style="display:none" id="packageList_navigation_link_template"><a class="active_trove_section_link"><strong></strong></a></div>
                  <div class="packageList_navigation_item" py:for="x in string.ascii_uppercase + '#'" id="troveList_${x}">${x}</div>
                </div>
                <div class="packageList_contents" id="packageList_troveList" style="display:none"/>
                <div class="packageList_contents" id="loading_wait" style="display:none">
                    <span style="float: right"><img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif"/></span>
                    The package list is loading, this may take a minute.
                </div>
            </div>
            <div class="packageList_submit">
                <input id="selectPackagesFormSubmit" value="Select Packages" type="Submit" disabled="disabled"/>
            </div>
            </form>
            <div>
              <a href="editApplianceGroup">Skip adding additional packages</a>
            </div>
        </div>
        </div>
    </body>
</html>
