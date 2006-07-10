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
                        <div class="boxhead"><span class="boxtitle">Builds</span></div>
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

                    <!-- /Builds -->

                    <div class="sidebox">
                        <div class="boxhead"><span class="boxtitle">More rPath Information</span></div>
                        <div class="boxbody">
                            <ul>
                                <li><div class="newsletterform">

                                    <form action="${cfg.corpSite}newsletter.cgi" method="post" id="newsletter">
                                    <p><label for="email">E-mail address: </label>
                                    <input type="text" name="email" value="" id="email" /></p>
				    <table border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                      <td><input class="reversed" type="checkbox" checked="checked" name="subscribe" value="1" id="subscribe" /></td>

				      <td><label class="reversed" for="subscribe">Subscribe to the newsletter</label></td>

				    </tr>
                                    <tr>
                                      <td><input class="reversed" type="checkbox" name="moreinfo" value="1" id="moreinfo" /></td>

                                      <td><label class="reversed" for="moreinfo">Request additional rPath build information</label></td>
                                    </tr>
                                    </table>
                                    <div>
                                    <button type="submit" class="img" id="newsletterSubmit">

                                        <img src="${cfg.corpSite}images/submit_button.png" alt="Submit" />
                                    </button>
                                    </div>
                                    </form>
                                    </div>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <!-- /Newsletter Signup -->
                </div>



                
        <p class="help" style="text-align: center;" py:if="not data">There are currently no appliances in the archive.  Please check back later.</p>
        <div style="width: 710px;" py:if="data">
        <?python import time ?>
            <h3 style="text-align: center;">rPath Virtual Appliance Spotlight Archive.  More guide text to follow.</h3>

        <div py:for="spotlightData in data">
        <p style="text-align: right; font-style: italic;">${time.strftime('%m/%d/%Y', time.localtime(spotlightData['startDate']))} - ${time.strftime('%m/%d/%Y', time.localtime(spotlightData['endDate']))}</p>
        <div onclick="location.href='${spotlightData['link']}'" id="spotlight">
 <div class="cssbox2">
        <div class="cssbox_head2">
            <div>&nbsp;</div>
        </div>
        <div class="cssbox_body2">
        <table>
        <tr>
        <td py:if="spotlightData['logo']" style="vertical-align: middle; width: 100px; text-align: center;" rowspan="3">
            <img id="applianceImg" src="${cfg.spotlightImagesDir}/${spotlightData['logo']}"/>
        </td>
	<td id="spotlightTitle">Virtual Appliance Spotlight</td>
	</tr>
	<tr>
        <td>
            <div id="applianceTitle">${spotlightData['title']}</div>
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

            <br/>
        </div>
        </div>
    </body>
</html>
