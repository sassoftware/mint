<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
import raa 
import raa.templates.master 
from raa.web import makeUrl, getConfigValue, inWizardMode
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
Copyright (c) 2006-2009 rPath, Inc.
    All Rights Reserved
-->

<head>
    <title>${getConfigValue('product.productName')}: Finalizing Initial rBuilder Setup</title>
    <style>
        #statusList {
                list-style-type: none;
                line-height: 2em;
                padding-left: 12px;
        }

        #statusList li {
                padding: 0 0 0 22px;
        }

        .currentState {
                font-weight: bold;
                background: url(${makeUrl('/rbasetup/static/images/wait.gif')}) left center no-repeat;
        }

        .completedState {
                font-weight: normal;
                background: url(${makeUrl('/rbasetup/static/images/check.gif')}) left center no-repeat;
        }
    </style>
    <script type="text/javascript" src="${makeUrl('/static/javascript/constants.js')}?v=25" />
    <script type="text/javascript" src="${makeUrl('/rbasetup/static/javascript/firstTimeSetup.js')}?v=1" />
</head>

<body>
    <div class="plugin-page" id="plugin-page">
        <div class="page-content">
            <form id="page_form" name="page_form" action="finalize" method="POST">
                <div class="page-section">
                    Finalizing Initial rBuilder Setup
                </div>
                <div class="page-section-content">
                    <p>Finalizing the initial setup of rBuilder. Please be patient as this may take some time.</p>
                    <p>Once this process has completed, click Continue and login to your rBuilder using the administrator username and password you specified.</p>
                    <ul id="statusList">
                        <li id="statusList_step1" class="currentState">Creating initial rBuilder administrative account</li>
                        <li id="statusList_step2">Configuring rMake</li>
                        <li id="statusList_step3">Setting up initial platforms</li>
                    </ul>
                </div>
                <div class="page-section-content-bottom">
                    <a class="rnd_button float-right off" id="continue_button" href="javascript:void(0);">Continue</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
