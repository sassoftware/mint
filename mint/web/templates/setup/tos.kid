<?xml version='1.0' encoding='UTF-8'?>
<?python
from conary.lib.cfg import *
from mint.web.templatesupport import projectText
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>rBuilder Terms of Service</title>
    </head>
    <body>
        <div class="layout">
            <h1>rBuilder Terms of Service</h1>

            <p>
                IMPORTANT! PLEASE READ THESE TERMS OF SERVICE CAREFULLY BEFORE 
                DOWNLOADING ANY MATERIAL OR USING ANY OF THE SOFTWARE PROVIDED 
                BY RPATH.  BY CLICKING “ACCEPT”, YOU AGREE TO BE BOUND BY THE 
                TERMS AND CONDITIONS CONTAINED HEREIN.  IF YOU DO NOT AGREE TO 
                BE BOUND BY THE TERMS AND CONDITIONS, DO NOT CLICK "ACCEPT", 
                REMOVE ALL RPATH-PROVIDED SOFTWARE FROM THIS COMPUTER, AND 
                RETURN ALL RPATH-PROVIDED MEDIA TO RPATH, INC.
            </p>
            <p>
                <strong>EXISTING CUSTOMERS:</strong>
                These terms and conditions do not apply to customers of rPath 
                since customers have already licensed the rPath technology by 
                execution of a Software Partner Agreement (or similar agreement)
                prior to this download.  
            </p>
            <p>
                <strong>EVALUATION PARTICIPANTS:</strong>
                If you are installing this Software as part of an evaluation, 
                the following terms and conditions apply to you:
            </p>
            <p>
                This is an evaluation version of the Software for internal, 
                non-commercial use only for a period of sixty (60) days and may 
                not be used for any other purpose.  The evaluation period may 
                not be extended by re-installing the software by downloading a 
                new evaluation copy of the software without the express written 
                consent of an authorized representative of rPath.  No other 
                rights, other than for evaluation of the software, are granted 
                hereunder.
            </p>
            <p>
                These terms and conditions shall no longer apply upon execution 
                of a Software Partner Agreement with terms acceptable to rPath.
            </p>

            <form action="processTos" method="post">
                <input type="hidden" name="acceptTos" value="True" />
                <p>
                    <button type="submit" class="img" id="theButton">
                        <img src="${cfg.staticPath}apps/mint/images/accept_button.png" alt="Accept" />
                    </button>
                </p>
            </form>
        </div>
    </body>
</html>
