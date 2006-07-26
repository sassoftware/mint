<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle("Appliance Spotlight")}</title>
        <link href="${cfg.corpSite}css/corp.css" type="text/css" rel="stylesheet" />
    </head>
    <body>
                <div id="right" class="side">
                    <!-- Try rBuilder -->
                    <div class="sidebox" id="tryitnow">
                        <a href="/rbuilder/">
                        <div class="boxhead-orange"><span class="boxtitle">Free! Sign up now <img src="${cfg.corpSite}images/small-arrow-orange.gif" alt="" width="11" height="10" /></span></div>
                        <div class="boxbody">

                            <br />
                            <img src="${cfg.corpSite}images/try-rBuilder-online.gif" alt="rBuilder" width="180" height="64" /><br />
                        </div>
                        </a>
                    </div>
                    <!-- /Try rBuilder -->
                    <!-- Builds -->
                    <div class="sidebox">
                        <div class="boxhead"><span class="boxtitle">Products</span></div>
                        <div class="boxbody">
                            <ul>
                                <li><span class="prodtitle"><a href="${cfg.corpSite}builds-rbuilder.html">rBuilder&trade;</a></span>
                                    rBuilder gives software developers the ability to turn their application into a Linux software
                                    appliance.<br />

                                    <a href="${cfg.corpSite}builds-rbuilder.html">Learn more</a></li>
                                <li><span class="prodtitle"><a href="${cfg.corpSite}builds-rpath-linux.html">rPath Linux&trade;</a></span>
                                    rPath Linux provides the stable foundation for building software appliances.<br />
                                    <a href="${cfg.corpSite}builds-rpath-linux.html">Learn more</a></li>
                            </ul>
                        </div>
                    </div>

                    <!-- /Products -->
<!-- Resources -->
                    <div class="sidebox">
                        <div class="boxhead"><span class="boxtitle">Resources</span></div>
                        <div class="boxbody">

                            <ul>
                                <li><strong>Product Review:</strong><br />
                                    <img src="${cfg.corpSite}images/pdficon_small.gif" alt="pdf" />
                                    <a href="${cfg.corpSite}docs/LinuxWorld_rPath_Product_Review.pdf">
                                        LinuxWorld Reviews rBuilder Online
                                    </a>
                                </li>
                                <li><strong>Analyst Report:</strong><br />

                                    <img src="${cfg.corpSite}images/pdficon_small.gif" alt="pdf" />
                                    <a href="${cfg.corpSite}docs/451-rPath_Impact_Report.pdf">
                                        451 rPath Impact Report
                                    </a>
                                </li>
                                <li><strong>Datasheet:</strong><br />
                                    <img src="${cfg.corpSite}images/pdficon_small.gif" alt="pdf" />
                                    <a href="${cfg.corpSite}docs/ISV-Partner.pdf">
                                        ISV Appliance Program
                                    </a>

                                </li>
                                <li><strong>Whitepaper:</strong><br />
                                    <img src="${cfg.corpSite}images/pdficon_small.gif" alt="pdf" />
                                    <a href="${cfg.corpSite}docs/rPath_Technology_Overview.pdf">
                                        Repository Based Systems Management
                                    </a>
                                </li>
                                <li><strong>Fact sheet:</strong><br />

                                    <img src="${cfg.corpSite}images/pdficon_small.gif" alt="pdf" />
                                    <a href="${cfg.corpSite}docs/rPath_Corporate_Overview.pdf">
                                        rPath Corporate Overview
                                    </a>
                                </li>
                                <li><strong>Press Coverage:</strong><br />
                                    <img src="${cfg.corpSite}images/pdficon_small.gif" alt="pdf" />
                                    <a href="${cfg.corpSite}docs/rPath_in_the_News.pdf">
                                        rPath in the News
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <!-- /Resources -->
                </div>



                
        <p class="help" style="text-align: center;" py:if="not data">There are currently no appliances in the archive.  Please check back later.</p>
        <div style="width: 710px;" py:if="data">
        <?python import time ?>
            <h2 style="text-align: center;">Virtual Appliance Spotlight Archive</h2>

        <div py:for="spotlightData in data" style="margin-top: 0px;">
        <div onclick="location.href='${spotlightData['link']}'" id="spotlight">
 <div class="cssbox2_archive">
        <div class="cssbox_head2">
        <div style="text-align: right; font-style: italic;">${time.strftime('%m/%d/%Y', time.localtime(spotlightData['startDate']))} - ${time.strftime('%m/%d/%Y', time.localtime(spotlightData['endDate']))}</div>
        </div>
        <div class="cssbox_body2">
        <table>
        <tr>
        <td py:if="spotlightData['logo']" style="vertical-align: middle; width: 100px; text-align: center;" rowspan="3">
            <img id="applianceImg" src="${cfg.spotlightImagesDir}/${spotlightData['logo']}"/>
        </td>
	<td id="spotlightTitle">${spotlightData['title']}</td>
	</tr>
	<tr>
        <td>
            <div id="applianceText">${spotlightData['text']}</div>
	</td>
	</tr>
	<tr>
	<td style="vertical-align: bottom;">
            <div id="applianceInfo">Click for more information.</div>
        </td>
        </tr>
        </table>
        </div>
        </div>
        </div>
        </div>
        </div>
    <div py:if="showNext or showPrev" style="text-align: center;">
    Page:
    <span py:for="page in range(pageCount)" style="margin-left: 5px; margin-right: 5px;"><a py:if="page + 1 != pageId" href="${cfg.basePath}applianceSpotlight?pageId=${page + 1}">${page + 1}</a><b style="margin-right: 2px; margin-left: 2px;" py:if="page + 1 == pageId">${page + 1}</b></span>
    <a py:if="showPrev" style="margin-left: 5px;" href="${cfg.basePath}applianceSpotlight?pageId=${pageId - 1}"><img src="${cfg.staticPath}apps/mint/images/prev.gif"/></a>
    <a py:if="showNext" style="margin-left: 5px;" href="${cfg.basePath}applianceSpotlight?pageId=${pageId + 1}"><img src="${cfg.staticPath}apps/mint/images/next.gif"/></a>
    </div>
    </body>
</html>
