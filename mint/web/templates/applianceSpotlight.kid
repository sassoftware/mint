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
<link href="http://www.rpath.com/corp/css/mint.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.com/corp/css/contentTypes.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.com/corp/css/corp.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.com/favicon.ico" rel="shortcut icon" />
        <link href="http://www.rpath.com/favicon.ico" rel="icon" />

        <style type="text/css">
            div#applianceBox {
                border-width: 4px;
                border-style: solid;
                border-color: #0033cc;
                background:   #dddddd;
                width:        615px;
            }
        </style>
    </head>
    <body onload="roundElement('applianceBox', {border: true});">
                <div id="right" class="side">
                    <!-- Try rBuilder -->
                    <div class="sidebox" id="tryitnow">
                        <a href="/rbuilder/">
                        <div class="boxhead-orange"><span class="boxtitle">Free! Sign up now <img src="http://www.rpath.com/corp/images/small-arrow-orange.gif" alt="" width="11" height="10" /></span></div>
                        <div class="boxbody">

                            <br />
                            <img src="http://www.rpath.com/corp/images/try-rBuilder-online.gif" alt="rBuilder" width="180" height="64" /><br />
                        </div>
                        </a>
                    </div>
                    <!-- /Try rBuilder -->
                    <!-- Software Appliance -->
                    <div class="sidebox">
                        <div class="boxhead"><span class="boxtitle">Software Appliance</span></div>

                        <div class="boxbody">
                            <ul>
                                <li>Brings the simplicity and value of Software as a Service (SaaS)
                                    to on-premise applications.<br />
                                    <a href="products-software-appliance.html">Learn more</a></li>
                            </ul>
                        </div>
                    </div>
                    <!-- /Software Appliance -->

                    <!-- Products -->
                    <div class="sidebox">
                        <div class="boxhead"><span class="boxtitle">Products</span></div>
                        <div class="boxbody">
                            <ul>
                                <li><span class="prodtitle"><a href="products-rbuilder.html">rBuilder&trade;</a></span>
                                    rBuilder gives software developers the ability to turn their application into a Linux software
                                    appliance.<br />

                                    <a href="products-rbuilder.html">Learn more</a></li>
                                <li><span class="prodtitle"><a href="products-rpath-linux.html">rPath Linux&trade;</a></span>
                                    rPath Linux provides the stable foundation for building software appliances.<br />
                                    <a href="products-rpath-linux.html">Learn more</a></li>
                            </ul>
                        </div>
                    </div>

                    <!-- /Products -->

                    <div class="sidebox">
                        <div class="boxhead"><span class="boxtitle">More rPath Information</span></div>
                        <div class="boxbody">
                            <ul>
                                <li><div class="newsletterform">

                                    <form action="newsletter.cgi" method="post" id="newsletter">
                                    <p><label for="email">E-mail address: </label>
                                    <input type="text" name="email" value="" id="email" /></p>
				    <table border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                      <td><input class="reversed" type="checkbox" checked="checked" name="subscribe" value="1" id="subscribe" /></td>

				      <td><label class="reversed" for="subscribe">Subscribe to the newsletter</label></td>

				    </tr>
                                    <tr>
                                      <td><input class="reversed" type="checkbox" name="moreinfo" value="1" id="moreinfo" /></td>

                                      <td><label class="reversed" for="moreinfo">Request additional rPath product information</label></td>
                                    </tr>
                                    </table>
                                    <div>
                                    <button type="submit" class="img" id="newsletterSubmit">

                                        <img src="http://www.rpath.com/corp/images/submit_button.png" alt="Submit" />
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



                
        <div align="center" style="width: 710px;">
            <h3>rPath Virtual Appliance Winners.  More guide text to follow.</h3>
            <div style="text-align: right; padding-right: 50px; font-style: italic;">June 6, 2006</div>
            <div>
                <img style="padding-top: 4px; padding-bottom: 20px;" src="${cfg.staticPath}apps/mint/images/port25.png" alt="Port25" />
            </div>
            <div style="text-align: right; padding-right: 50px; font-style: italic;">June 6, 2006</div>
            <div>
                <img style="padding-top: 4px; padding-bottom: 20px;" src="${cfg.staticPath}apps/mint/images/port25.png" alt="Port25" />
            </div>
            <div style="text-align: right; padding-right: 50px; font-style: italic;">June 6, 2006</div>
            <div>
                <img style="padding-top: 4px; padding-bottom: 20px;" src="${cfg.staticPath}apps/mint/images/port25.png" alt="Port25" />
            </div>
        </div>
    </body>
</html>
