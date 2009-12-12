<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
Copyright (c) 2006-2010 rPath, Inc.
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
  instructions = """IMPORTANT! PLEASE READ THESE TERMS OF SERVICE (\"TOS\") CAREFULLY BEFORE DOWNLOADING ANY MATERIAL OR USING ANY OF THE SOFTWARE PROVIDED BY RPATH.  BY CHECKING \"ACCEPT\", YOU AGREE TO BE BOUND BY THE TERMS AND CONDITIONS CONTAINED HEREIN.  IF YOU DO NOT AGREE TO BE BOUND BY THE TERMS AND CONDITIONS, DO NOT CHECK \"ACCEPT\"."""
?>
<div class="plugin-page" id="plugin-page">
     <div class="page-content">
         <div py:replace="display_instructions(instructions, raaInWizard)"/>
     </div>
     <div py:if="raaInWizard" class="page-section">rBuilder Terms of Service</div>
     <div class="page-section-content-bottom">

        <p>
        The Software (rBuilder&#174; and the Lifecycle Management Software&#8482;) is provided in the sole discretion of rPath&#174; at no 
        cost to you solely for internal use with the following limitations:
        </p>
        
        <p>
        GRANT OF LICENSE:
        </p>
        
        <p>
        rPath hereby grants to you a non-exclusive, personal license to use the Software and any related documentation (&quot;Documentation&quot;) 
        subject to the following terms:
        </p>

        <p>
        a)  You may: (i) use the Software on any single Computer; and (ii) copy the Software for back-up and archival purposes, provided any 
        copy must contain all of the original Software's proprietary notices within the United States and its territories or any other country 
        to which this Software can legally be exported.
        </p>

        <p>
        b)  The Software is &quot;in use&quot; on a computer when it is loaded into temporary memory or installed in permanent memory (Hard Drive,
        CD-ROM or other storage device).  You agree to use your best efforts to prevent and protect the contents of the Software and Documentation
        from unauthorized use or disclosure.  You agree that you will register this Software and its Serial Number only with rPath and that you 
        will only install a Software entitlement obtained directly from rPath.
        </p>

        <p>
        c)  You can only manage up to twenty (20) Running Instances.  "Running Instance" is an Application Image which is deployed and managed by 
        the Software.  "Application Image" means a combination of an application and third party software that is created by the Software.
        </p>

        <p>
        d)  At certain time intervals and in the sole discretion of rPath, you will be required to renew your key with rPath.  Failure to renew 
        your key when required will immediately terminate your rights to use the Software under this TOS.
        </p>

        <p>
        LICENSE RESTRICTIONS.
        </p>
        
        <p>
        a)  You may not: (i) permit other individuals to use the Software except under the terms listed above; (ii) modify, translate, reverse 
        engineer, decompile, disassemble (except to the extent that this restriction is expressly prohibited by law) or create derivative works 
        based upon the Software or Documentation; (iii) copy the Software or Documentation (except for back-up or archival purposes); (iv) rent, 
        lease, transfer, or otherwise transfer rights to the Software or Documentation; (v) remove any proprietary notices or labels on the 
        Software or Documentation. Any such forbidden use shall immediately terminate your license to the Software. The recording, playback and 
        download features of the Software are intended only for use with public domain or properly licensed content and content creation tools. 
        You may require a patent, copyright, or other license from a third party to create, copy, download, record or save content files for 
        playback by this Software or to serve or distribute such files to be played back by the Software.
        </p>
        
        <p>
        b)  You agree that you shall only use the Software and Documentation in a manner that complies with all applicable laws in the 
        jurisdictions in which you use the Software and Documentation, including, but not limited to, applicable restrictions concerning 
        copyright and other intellectual property rights.
        </p>
        
        <p>
        OWNERSHIP: 
        </p>
        
        <p>
        Title, ownership, rights, and intellectual property rights in and to the Software and Documentation shall remain rPath’s and/or its 
        suppliers.  The Software and the Documentation are protected by the copyright laws of the United States and international copyright 
        treaties.  Title, ownership rights and intellectual property rights in and to the content accessed through the Software and the 
        Documentation (&quot;Content&quot;) shall be retained by the applicable Content owner and may be protected by applicable copyright or 
        other law.  This TOS gives you no rights to such Content.
        </p>
        
        <p>
        NO WARRANTY: 
        </p>
        
        <p>
        RPATH PROVIDES THE SOFTWARE WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED 
        WARRANTIES OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE OR WARRANTIES OF QUALITY OR PERFORMANCE, OR WARRANTIES OF 
        NON-INFRINGEMENT.
        </p>
        
        <p>
        DATA RIGHTS:
        </p>
        
        <p>
        You should be aware that rPath's Software contains functions for collecting information related to your use of the Software.  rPath may 
        also collect and track non-personally identifiable information about you including but not limited to your IP address, the type of 
        hardware you use and the type of browser you employ.  rPath reserves the right to compile, save, use within the scope of rPath’s 
        activities, and analyze any and all of your data (registration data, and use history).  rPath intends to use such data for internal 
        purposes only, including without limitation for the purposes of responding to your requests for information and for contacting you.  
        rPath may provide aggregated statistics about your use of the Software to third parties, but such information will be aggregated so 
        that it does not identify a particular individual or company.
        </p>

        <p>
        NO LIABILITY: 
        </p>
        
        <p>
        TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT WILL rPATH, INC. BE LIABLE TO END USER FOR ANY DAMAGES OF ANY KIND SUCH 
        AS ACTUAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, LOST SAVINGS, OR OTHER INCIDENTAL OR CONSEQUENTIAL DAMAGES, 
        ARISING OUT OF THE USE OR INABILITY TO USE THE SOFTWARE OR SOFTWARE PROGRAMS, EVEN IF rPATH, INC. OR A DEALER AUTHORIZED BY rPATH, INC. 
        HAD BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.  IN NO EVENT SHALL rPATH HAVE ANY LIABILITY HEREUNDER.
        </p>

        <p>
        REVOCATION OF KEY:
        </p>
        
        <p>
        In the sole discretion of rPath, rPath reserves the right at any time for any reason or no reason to terminate your key and your rights 
        to use the Software and Documentation without notice of any kind.
        </p>

        <p>
        THIRD-PARTY SOFTWARE:
        </p>
        
        <p>
        You agree that your use of any third party software included in the Software shall be governed by such third party's license agreement. 
        rPath is not responsible or liable for any third party software.
        </p>
        
        <p>
        COMPLETE AGREEMENT:
        </p>
        
        <p>
        Except as provided below under "Conflict", this TOS constitutes the entire agreement between the parties with respect to the Software and 
        supersedes all prior or contemporaneous communications, agreements and understandings, written or oral, with respect to the subject 
        matter hereof.  This TOS shall not be amended or modified except in a writing signed by authorized representatives of each party.
        </p>

        <p>
        GENERAL:
        </p>
        
        <p>
        If any provision of this TOS is held to be unenforceable, that shall not affect the enforceability of the remaining provisions.  This 
        TOS shall be governed by the laws of the State of North Carolina and of the United States, without regard to any conflict of laws 
        provisions, except that the United Nations Convention on the International Sale of Goods shall not apply.
        </p>

        <p>
        CONFLICT:
        </p>
        
        <p>
        If these terms and conditions explicitly conflict with the provisions of any other agreement now or in the future existing between 
        Customer and rPath that grants Customer a license to use any of the Software, the provisions of such other agreement will prevail 
        over the terms of this TOS.
        </p>

        <p>
        Copyright &#169; 2005 - 2010.  rPath, Inc.  All rights reserved.
        </p>
        
        <p>
        &quot;rPath,&quot; "rPath" Logo, "Powered by rPath" Logo, "rPath Lifecycle Management Platform" logo, "Conary,"  "rMake," "rBuilder," and "rBuilder" Logo are trademarks and service marks that are the property of rPath, Inc.
        </p> 

        <p>
        Revised April 14, 2009
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
