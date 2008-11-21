<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
Copyright (c) 2006-2008 rPath, Inc.
    All Rights Reserved
-->

<head>
    <title>rBuilder Terms of Service</title>
    <?python
  from raa.web import makeUrl
    ?>
</head>

<body>
<?python
  instructions = """IMPORTANT! PLEASE READ THESE TERMS OF SERVICE CAREFULLY BEFORE DOWNLOADING ANY MATERIAL OR USING ANY OF THE SOFTWARE PROVIDED BY RPATH. BY CLICKING “ACCEPT”, YOU AGREE TO BE BOUND BY THE TERMS AND CONDITIONS CONTAINED HEREIN. IF YOU DO NOT AGREE TO BE BOUND BY THE TERMS AND CONDITIONS, DO NOT CLICK "ACCEPT", REMOVE ALL RPATH-PROVIDED SOFTWARE FROM THIS COMPUTER, AND RETURN ALL RPATH-PROVIDED MEDIA TO RPATH, INC."""
?>
<div class="plugin-page" id="plugin-page">
     <div class="page-content">
         <div py:replace="display_instructions(instructions, raaInWizard)"/>
     </div>
     <div py:if="raaInWizard" class="page-section">rBuilder Terms of Service</div>
     <div class="page-section-content-bottom">

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

    <br/><br/>
    <div py:if="not raaInWizard" style="text-align: center"><strong>*** These terms of service have already been accepted. ***</strong></div>
    <form py:if="raaInWizard" action="javascript:void(0);" method="POST" id="page_form" name="page_form"
	    onsubmit="javascript:postFormWizardRedirectOnSuccess(this,'saveConfig');">
	    <a class="rnd_button float-right" id="OK" href="javascript:button_submit(document.page_form)">Accept</a>
    </form>
    </div>
</div>
</body>
</html>
