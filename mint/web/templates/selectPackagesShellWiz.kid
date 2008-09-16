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
        <title>${formatTitle('Select Packages: %s' % project.getNameForDisplay())}</title>
    </head>
    <body>
        <div class="fullpage">
            <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div id="left" class="side">
                ${wizard_navigation()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            
            <div id="fullpage-middle">
                
                <div class="edit-version">
                    Version: ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</div>
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>    
                <div class="page-title">Appliance Creator</div>    
                
                <p py:if="message" class="message" py:content="message"/>
                
                <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/packagelist.js?v=${cacheFakeoutVersion}" />
                <h2>Select Additional Packages</h2>
                <p>If there are additional packages you would like your appliance to contain, select them from the list below.</p>
                <div id="jumpto_box">    
                    <span>
                        <label for="jumpto">Type a filter term: </label>
                        <input name="jumpto" id="jumpto_box" value="" disabled="disabled"/>
                        <input id="jumpto_box_clear" type="image" src="${cfg.staticPath}apps/mint/images/clear_filter.gif" title="Clear Filter"/>
                    </span>
                </div>
                
                <div id="filter_selections" style="display:none"/>
                
                <div id="filter_navigation_link_template" style="display:none"></div>
                
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
                    <input id="selectPackagesFormSubmit" value="Continue" type="Submit"/>
                </div>
                </form>
            </div>
            <br class="clear"/>
            <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
