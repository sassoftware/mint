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
     <div py:if="raaInWizard" class="page-section">rPath Cloud Engine Terms of Service</div>
     <div class="page-section-content-bottom">

        <p>
        <b>
        1.  INTRODUCTION
        </b>
        </p>
        
        <p>
        PERMISSION TO DOWNLOAD, INSTALL AND USE THE SOFTWARE IS CONDITIONED UPON YOU, THE END USER OF THE SOFTWARE (“END USER”), AGREEING TO THIS END USER LICENSE AGREEMENT (“EULA”) WHICH IS BETWEEN RPATH, 
        INC. (“RPATH”) AND END USER.  THIS EULA SHALL GOVERN END USER’S USE OF THE SOFTWARE AND DOCUMENTATION.  CAPITALIZED TERMS NOT OTHERWISE DEFINED HEREIN ARE DEFINED IN SECTION 10.1.
        </p>
        
        <p>
        INSTALLATION OR USE OF THE SOFTWARE BY END USER WILL BE DEEMED ACCEPTANCE OF THIS EULA. IF END USER DOES NOT ACCEPT THE TERMS OF THIS EULA, OR HAVE THE AUTHORITY TO ENTER INTO THIS EULA, END USER 
        MAY NOT DOWNLOAD, INSTALL OR USE THE SOFTWARE.  IF YOU ARE INSTALLING AND USING THIS SOFTWARE ON BEHALF OF AN END USER WHICH IS A CORPORATION, PARTNERSHIP, OR OTHER LEGAL ENTITY, SUCH AS YOUR
        EMPLOYER, YOU REPRESENT AND WARRANT TO RPATH THAT YOU ARE AUTHORIZED TO ENTER INTO THIS EULA AND ACCEPT THESE TERMS ON BEHALF OF END USER. ACCEPTANCE WILL BIND END USER TO THESE LICENSE TERMS 
        IN A LEGALLY ENFORCEABLE CONTRACT WITH RPATH, AND END USER AGREES THAT THIS EULA SHALL BE AS ENFORCEABLE AS A SIGNED WRITTEN AGREEMENT.  
        </p>
        
        <p>
        INDIVIDUAL THIRD-PARTY SOFTWARE COMPONENTS, EACH OF WHICH HAS ITS OWN COPYRIGHT AND ITS OWN APPLICABLE LICENSE CONDITIONS (“THIRD PARTY SOFTWARE”) MAY BE DISTRIBUTED, EMBEDDED, OR BUNDLED WITH THE
        SOFTWARE. SUCH THIRD PARTY SOFTWARE IS SEPARATELY LICENSED BY ITS COPYRIGHT HOLDER. USE OF THE THIRD PARTY SOFTWARE MUST BE IN ACCORDANCE WITH ITS LICENSE TERMS. RPATH MAKES NO REPRESENTATION, 
        WARRANTY OR OTHER COMMITMENT OF ANY KIND REGARDING SUCH THIRD PARTY SOFTWARE, AND SHALL HAVE NO LIABILITY ASSOCIATED WITH ITS USE.
        </p>
        
        <p>
        <b>
        2.  Grant of License
        </b>
        </p>
        
        <p>
        2.1.  Subject to the terms and conditions of this EULA and the payment of all applicable license fees, rPath grants End User and its Permitted Affiliates, during the License Term, a limited, 
        non-exclusive, non-transferable license to: (i) Use the Software in accordance with the Documentation; (ii) reproduce and use the Documentation in support of their licensed Use of the 
        Software; and (iii) make a reasonable number of copies of the Software solely for back-up and archival purposes.  End User shall maintain an up-to-date written record of the number of copies 
        of the Software in its possession and, upon request, shall produce such record to rPath.  End User shall ensure that all reasonable precautions are taken to safeguard the Software and the 
        Documentation to prevent their misuse.2.2.    Permitted Affiliates and Authorized Contractors. 2.2.1.  Third-party contractor(s) or service provider(s) authorized by End User to perform 
        services for End User or its Permitted Affiliates (“Authorized Contractor”), may access and use the Software and the Documentation but only for End User’s and its Permitted Affiliates’ 
        internal business operations and activities, subject to all of the terms, conditions and restrictions set forth in this EULA and the Documentation.2.2.2.  In connection with the use of the 
        Software by a Permitted Affiliate and/or Authorized Contractor(s), End User hereby agrees to: (i) make each such Permitted Affiliate and/or Authorized Contractor aware of the terms of this 
        EULA and the Documentation, including, without limitation, the use limitations contained in Sections 2.1 and 2.3; (ii) monitor each such Permitted Affiliate’s and/or Authorized Contractor’s
        compliance with the terms contained in this EULA and in the Documentation; and (iii) remain responsible and directly liable to rPath for any and all violations of the terms contained in this 
        EULA and in the Documentation by any Permitted Affiliate or Authorized Contractor.  Upon request by rPath, End User agrees to confirm the Affiliate status of a Permitted Affiliate.   A 
        Permitted Affiliate of End User is permitted to use the Software only for so long as such entity is an Affiliate as defined in Section 10.1.
        </p>

        <p>
        2.3.  License Restrictions.  Except as expressly provided herein and except to the extent required by local copyright or other laws whose application is incapable of exclusion by agreement, 
        End User shall not: (i) use, copy, maintain, distribute, sell, market, sublicense, rent, make corrections to modify, adapt or translate the Software; (ii) reverse assemble, reverse compile, 
        reverse engineer or otherwise translate the Software;  (iii) combine or merge any part of the Software or the Documentation with or into any other software or documentation; (iv) use or 
        sublicense the Software for the benefit of a third party or in a service bureau, commercial time-sharing, rental, software as a service (SaaS), or outsourcing context except where previously 
        agreed in writing by rPath; or (v) provide the Software or the Documentation to any entity or person other than a Permitted Affiliate or an Authorized Contractor unless otherwise  agreed in 
        writing by rPath.  If a serial number, password, license key or other security device is provided to End User for use with the Software, End User may not, and will not permit its authorized 
        users to, share or transfer such security device with or to any other user of the Software or any other third party.
        </p>
        
        <p>
        2.4.  Retention of Rights. The Software and the Documentation are licensed, not sold. rPath and its Affiliates, or their respective suppliers or licensors where applicable, own and retain all
        right, title and interest in and to the Software and the Documentation, and all of rPath’s and its Affiliates’, or their respective suppliers’ or licensors’, patents, trademarks (registered 
        or unregistered), trade names, copyrights, trade secrets and rPath Confidential Information.  End User does not acquire any right, title or interest in or to the Software or the Documentation
        except as expressly set forth herein.
        </p>
        
        <p>
        <b>
        3.  Maintenance
        </b>
        </p>
        
        <p>
        Subject to the payment of all applicable maintenance and support fees, any maintenance of the Software (i.e. technical support and Updates) will be provided either directly by rPath pursuant 
        to its then current Maintenance Policy, or in accordance with a separate written maintenance agreement between End User and an Authorized rPath Reseller, or other representative(s) authorized 
        by rPath to provide maintenance and support services for the Software.
        </p>
        
        <p>
        <b>
        4.  Limited Warranties and Disclaimers
        </b>
        </p>
        
        <p>
        4.1.  Limited Warranties.  
        </p>
        
        <p>
        4.1.1.  Performance Warranty. rPath warrants that, for a period of ninety (90) days following the Delivery Date (the “Warranty Period”), the initial version of the Software provided to End User 
        hereunder (excluding any subsequent Updates thereto) will perform substantially in accordance with the specifications in the applicable Documentation in effect on the Delivery Date, provided 
        that the Software is operated in accordance with the Documentation. End User must report any alleged non-conformance of the warranty contained in Section 4.1.1 to rPath in writing during the 
        Warranty Period.  End User’s exclusive remedy and rPath’s sole liability with regard to any breach of the warranty contained in this Section 4.1.1 shall be, at rPath's option and expense, to 
        either: (i) repair or replace the non-conforming Software; or (ii) refund to End User the license and any prepaid maintenance and support fees paid by End User for the non-conforming Software. 
        If rPath elects to return the applicable license and any maintenance and support fees paid for the non-conforming Software pursuant to Section 4.1.1(ii) above: (a) End User shall promptly return
        the non-conforming Software to rPath or establish to rPath’s reasonable satisfaction that it has destroyed/uninstalled the applicable Software; and (b) the licenses granted to End User hereunder
        in respect of such non-conforming Software and associated Documentation shall automatically terminate.
        </p>
        
        <p>
        4.1.2.  Anti-virus Warranty. rPath warrants that it will use commercially available 
        third-party virus detection software to test the Software provided under this Agreement for any Unauthorized Code prior to delivery to End User.  End User must notify rPath in writing of any 
        breach of the foregoing warranty promptly following discovery. Further, End User will cooperate with rPath and provide rPath all information available to End User that is relevant to verifying, 
        diagnosing or correcting the breach.  rPath shall have no liability for any breach of the foregoing warranty to the extent that any damages suffered or incurred by End User could have been 
        avoided by End User's implementation of commercially reasonable precautions to monitor its own systems for Unauthorized Code. End User shall take commercially reasonable measures to mitigate any
        damages suffered or incurred by End User as a result of a breach of the warranty set forth in this Section.
        </p>
        
        <p>
        4.2.  Disclaimers.   THE LIMITED WARRANTIES STATED IN SECTION 4.1 SET FORTH THE ONLY REPRESENTATIONS AND WARRANTIES CONCERNING THE SOFTWARE AND THE DOCUMENTATION.  RPATH AND ITS SUPPLIERS 
        DISCLAIM ALL OTHER WARRANTIES, CONDITIONS AND OTHER TERMS, WHETHER EXPRESS OR IMPLIED (BY STATUTE, COMMON LAW OR OTHERWISE) INCLUDING WITHOUT LIMITATION, AS TO TITLE, NON-INFRINGEMENT, 
        MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, EVEN IF RPATH HAS BEEN INFORMED OF SUCH PURPOSE, AND ANY REPRESENTATIONS, WARRANTIES OR OTHER TERMS ARISING FROM COURSE OF PERFORMANCE, 
        COURSE OF DEALING, OR USAGE OF TRADE.
        </p>
        
        <p>
        <b>
        5.  Limitation of Liability
        </b>
        </p>
        
        <p>
        5.1.  Limitations of Liability
        </p>
        
        <p>
        5.1.1.  Except for rPath’s obligations with respect to any Third-party IP Claim as provided in Section 6.1 (Indemnification of Third-party IP Claims), rPath’s and its Affiliates’ aggregate 
        and cumulative liability for damages (regardless of the form of action, whether in contract, tort or otherwise) shall in no event exceed the amount of fees paid by End User for the Software 
        in respect of which the claim arose and, if such damages relate to particular Software, such liability shall be limited to the fees paid for such Software. 
        </p>
        
        <p>
        5.1.2.  Except for End User’s: (i) non-compliance with the use restrictions contained within this EULA or violation of rPath’s intellectual property rights; (ii) breach of its obligations 
        pursuant to Section 8 (Confidentiality);  (iii) breach of its obligations under Section 10.4 (Compliance with Laws); (iv) negligence resulting in death or personal injury; and/or (v) fraud 
        or intentional misconduct, End User’s aggregate and cumulative liability for damages, regardless of the form of action, whether in contract, tort or otherwise, shall in no event exceed the 
        amounts paid and payable by End User for the Software in respect of which the claim arose.
        </p>
        
        <p>
        5.1.3.  No Consequential Damages. EXCEPT FOR END USER’S: (i) NON-COMPLIANCE WITH THE USE RESTRICTIONS CONTAINED WITHIN THIS EULA OR VIOLATION OF RPATH’S INTELLECTUAL PROPERTY RIGHTS; AND/OR 
        (ii) BREACH OF END USER’S OBLIGATIONS PURSUANT TO SECTION 8 (CONFIDENTIALITY), IN NO EVENT SHALL EITHER PARTY OR ITS AFFILIATES BE LIABLE FOR ANY LOSS OF PROFITS OR REVENUES, SAVINGS, GOODWILL, 
        DATA OR INACCURACY OF ANY DATA OR COST OF SUBSTITUTE GOODS OR SOFTWARE REGARDLESS OF THE THEORY OF LIABILITY OR FOR ANY INDIRECT, INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES OR LOSS, HOWSOEVER 
        ARISING, EVEN IF THE OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGE OR LOSS.
        </p>
        
        <p>
        5.2.  THE FOREGOING LIMITATIONS, EXCLUSIONS AND DISCLAIMERS SET FORTH IN THIS EULA SHALL APPLY TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, EVEN IF ANY REMEDY FAILS OF ITS ESSENTIAL PURPOSE.
        </p>
        
        <p>
        <b>
        6.  Indemnification of Third-party IP Claims
        </b>
        </p>
        
        <p>
        6.1.  Intellectual Property Infringement. Subject to the provisions of Sections 5.1, 6.2, 6.3 and 6.5, rPath will: (i) defend End User against any Third-party IP Claim, at rPath’s expense; and 
        (ii) pay to End User any and all direct damages, costs and expenses (including without limitation reasonable attorney’s fees) finally awarded against End User by a court of competent jurisdiction 
        (or agreed to in a written settlement agreement signed by rPath) to the extent directly attributable to any Third-party IP Claim.
        </p>
        
        <p>
        6.2.  Conditions. rPath’s indemnification obligations under Section 6.1 are subject to the following conditions: (i) End User will provide rPath with prompt written notice of any Third-party IP 
        Claim; (ii) End User will permit rPath to assume and control the defense and settlement of any Third-party IP Claim; (iii) End User will not prejudice the defense of any Third-party IP Claim; 
        (iv) End User will mitigate such damages, costs and expenses, as far as reasonably possible; and (v) End User will provide rPath with such assistance, documents, authority and information as 
        rPath may reasonably require in relation to any Third-party IP Claim and defense or settlement thereof.
        </p>
        
        <p>
        6.3.  Exceptions.  rPath will have no liability to End User under Section 6.1 for any Third-party IP Claim that: (i) arises out of any unauthorized use, reproduction, or distribution of the 
        Software or the Documentation by End User; (ii) arises out of any modification or alteration of the Software or the Documentation by anyone other than rPath without the written approval of rPath; 
        (iii) arises out of the use of the Software in combination with any other software or equipment; or (iv) would have been avoided by use of the then-current release of the Software.
        </p>
        
        <p>
        6.4.  rPath Option.  If the Software becomes, or in rPath’s opinion is likely to become, the subject of a Third-party IP Claim, rPath may, at its own expense and option, elect to either: (i) procure 
        the right for End User to continue using the Software in accordance with the provisions of this EULA; (ii) make such alterations, modifications or adjustments to the Software so that the infringing 
        Software becomes non-infringing without incurring a material diminution in performance or function; (iii) replace the Software with a non-infringing substantially similar substitute; or (iv) if 
        rPath determines in its discretion that neither (i), (ii) nor (iii) can be achieved after the exercise of commercially reasonable efforts, terminate the license for the affected Software and refund 
        to End User all amounts paid by End User as license fees with respect to the affected Software, less an amount equal to depreciation of such license fees calculated on a three-year straight-line 
        basis from the date of first license. Upon payment of any refund, End User acknowledges and agrees that the license for that Software will be deemed to have automatically terminated.
        </p>
        
        <p>
        6.5.  Sole and Exclusive Remedy. THE FOREGOING STATES RPATH’S ENTIRE OBLIGATION AND LIABILITY, AND END USER’S SOLE RIGHT AND REMEDY, FOR INFRINGEMENT OF THIRD-PARTY INTELLECTUAL PROPERTY RIGHTS.
        </p>

        <p>
        <b>
        7.  Termination
        </b>
        </p>
        
        <p>
        This EULA is effective until terminated as provided herein. End User may terminate this EULA for convenience at any time by notifying rPath in writing of its election to terminate this EULA and 
        uninstalling, destroying or returning to rPath all copies of the Software and the Documentation in End User’s possession or within its control; provided, however, that no such termination shall 
        entitle End User to a refund of any license fees or prepaid maintenance fees paid in respect of the applicable Software. rPath may terminate this EULA immediately at any time by written notice to 
        End User if End User has breached any of the terms of this EULA. Upon termination of this EULA, all license(s) granted hereunder shall immediately terminate. 
        </p>
        
        <p>
        Upon termination of any license (for any reason, whether due to termination of this EULA or as otherwise provided herein), End User shall promptly return all copies of the Software and the 
        Documentation to rPath or establish to rPath’s satisfaction that End User has uninstalled or destroyed all copies of the Software and the Documentation, including, without limitation, certifying in 
        writing that all known copies, including archival or backup copies, have been uninstalled, destroyed or returned to rPath.  All provisions relating to confidentiality, rPath’s ownership and proprietary
        rights, limitations of liability, disclaimers of warranties, waiver, and governing law and jurisdiction shall survive the termination of this EULA.  Termination shall not affect or prejudice either 
        party’s rights accrued as at the date of termination.
        </p>
        
        <p>
        <b>
        8.  Confidentiality
        </b>
        </p>
        
        <p>
        End User agrees to hold in confidence Confidential Information until End User receives written notice from rPath that the Confidential Information ceases to be confidential.  End User further agrees 
        that End User shall not use Confidential Information except to the extent necessary to exercise the license granted to End User by rPath hereunder. End User will protect Confidential Information 
        from unauthorized access, distribution and use with the same degree of care that End User uses to protect its own like information, but in no event less than a reasonable degree of care.  End User 
        acknowledges and agrees that, due to the unique nature of the Confidential Information, there can be no adequate remedy at law for breach of this Section and that such breach would cause irreparable 
        harm to rPath; therefore rPath will be entitled to seek immediate injunctive relief, in addition to any remedies otherwise available at law or under this EULA.
        </p>
        
        <p>
        <b>
        9.  Verification and Audit
        </b>
        </p>
        
        <p>
        9.1.  Verification. At rPath’s written request, but not more frequently than once annually, End User shall furnish rPath with a document signed by End User’s authorized representative verifying that 
        the Software is being used in accordance with the terms of this EULA and the Documentation.  In the event that End User is not in compliance with the terms of this EULA, End User shall promptly report a
        ny discrepancies in the verification document.  End User agrees to implement reasonable security controls to ensure compliance with the intended use of the Software authorized by this EULA.
        </p>
        
        <p>
        9.2.  Audit.  During the term of this EULA and for a period of one (1) year thereafter, upon rPath’s written request, but no more frequently than once per year, rPath or an independent and reputable agent 
        or accounting firm chosen by rPath will be provided reasonable access during End User’s normal business hours to examine End User’s records and computer equipment, at rPath’s expense, for the purpose of 
        auditing End User’s obligations under this EULA. rPath’s written request for audit will be submitted to End User at least fifteen (15) days prior to the specified audit date.  If End User is not in material 
        compliance with the terms of this EULA, End User shall reimburse rPath for the expenses incurred by rPath in conducting the audit.
        </p>
        
        <p>
        <b>
        10.  General Provisions 
        </b>
        </p>
        
        <p>
        10.1.  Definitions.
        </p>
        
        <p>
        10.1.1. “Affiliate” means any entity which controls, is controlled by, or is under common control with rPath or End User, as applicable, where “control” means the legal, beneficial or equitable ownership of 
        at least a majority of the aggregate of all voting equity interests in such entity.
        </p>
        
        <p>
        10.1.2. “Application Image” means a combination of and End User Product and Third Party Software that is created, deployed, managed and maintained by the Software.
        </p>
        
        <p>
        10.1.3. “Authorized rPath Reseller” means a reseller, dealer, or distributor authorized in writing by rPath to resell and distribute licenses for the Software.
        </p>
        
        <p>
        10.1.4. “Confidential Information” means any confidential or proprietary information which relates to rPath’s trade secrets, Software, source code for the Software, the Documentation, services, deliverables, 
        training materials, technology, research, development, pricing, product plans, marketing plans, business information, proprietary materials including visual expressions, screen formats, report formats, 
        design features, ideas, methods, algorithms, formulae, and concepts used in the design and all future modifications and enhancements.  Confidential Information includes third party data or information that 
        was disclosed to End User under a duty of confidentiality.  Confidential Information also includes any information, in whatever form, disclosed or made available by rPath to End User that relates to or is 
        contained within rPath Confidential Information and that is not publicly known.  Confidential Information does not include information that: (i) enters the public domain through no fault of End User; (ii) 
        is communicated to End User by a third party under no obligation of confidentiality; (iii) has been independently developed by End User without reference to any Confidential Information; (iv) was in End 
        User’s lawful possession prior to disclosure and had not been obtained either directly or indirectly from rPath; and (v) is required to be disclosed by law, provided End User has promptly notified rPath in 
        writing of such requirement and allowed rPath a reasonable time to oppose such requirement.
        </p>
        
        <p>
        10.1.5. “Covered Jurisdiction” means those countries who are contracting parties to the Berne Convention.
        </p>
        
        <p>
        10.1.6. “Delivery Date” means the date the Software is first delivered to or made available for download by End User or the Authorized rPath Reseller from whom End User ordered the license to the Software.
        </p>
        
        <p>
        10.1.7. “Deployed Instance” means any Application Image that is deployed to a test lab, production IT, co-location facility, training facility or a data center and was created, deployed, managed or maintained 
        using the Software.
        </p>
        
        <p>
        10.1.8. “Documentation” means the then-current end user documentation published and made generally available by rPath for the Software in the form of manuals and function descriptions in printed or electronic 
        form, as the same may be modified by rPath from time to time.  The terms contained in the Documentation are hereby incorporated into this Agreement by this reference.  A copy of the Documentation is available 
        upon the request of End User.
        </p>
        
        <p>
        10.1.9. “End User Product” means an application developed by or for End User for internal use or an off-the-shelf application developed by a third party which End User has licensed from a third party for 
        internal use.
        </p>
        
        <p>
        10.1.10.  “License Term” means the license term identified in the applicable Order Form.
        </p>
        
        <p>
        10.1.11.  “Maintenance Policy” means rPath’s then-current policy governing the provision by rPath of maintenance and technical support services (including Updates) for the Software, as the same may be amended 
        from time to time in the discretion of rPath.  A copy of the Maintenance Policy is available upon the request of End User.  All maintenance and support services provided by rPath are subject to the terms and 
        conditions of the Maintenance Policy, and End User agrees to be bound thereby. 
        </p>
        
        <p>
        10.1.12.  “Order Form” means a written order form or sales order pursuant to which End User orders a license for the Software, which specifies, at a minimum, the license fees for the Software and the applicable 
        License Term, and which is executed by End User and rPath (or an Authorized rPath Reseller).
        </p>
        
        <p>
        10.1.13.  “Permitted Affiliate” means an Affiliate of End User authorized by End User to use the Software and Documentation in accordance with the terms and conditions of this Agreement. 
        </p>
        
        <p>
        10.1.14.  “Software” means (i) the version of rPath’s proprietary rPath Cloud Engine software in object code form that accompanies and is licensed under this EULA, and (ii) any Updates thereto made generally 
        available to End Users who are current on their maintenance fees.
        </p>
        
        <p>
        10.1.15.  “Third-party IP Claim” means a claim or threatened claim brought by a third-party in a Covered Jurisdiction that the Software, unmodified and in the form originally delivered by rPath to End User or 
        the Authorized rPath Reseller from whom End User ordered the Software directly infringes any copyright or misappropriates any trade secret of such third-party recognized under the laws of the Covered 
        Jurisdiction, in each case in violation of the laws of the Covered Jurisdiction.
        </p>
        
        <p>
        10.1.16.  “Unauthorized Code" means any virus, Trojan horse, worm, or other routine or code designed to disable, erase, alter, or otherwise harm any computer system, program, database, data, hardware or 
        communications system in a manner which is malicious or intended to damage.
        </p>
        
        <p>
        10.1.17.  “Updates” means a new version or a new release of the Software that rPath makes generally available to its customers who are current on their maintenance fees, which may include, without limitation, 
        modifications and enhancements; provided, however, that Updates shall not include new or separate products which rPath offers only for an additional fee to its customers generally, including those customers 
        purchasing maintenance.
        </p>
        
        <p>
        10.1.18.  “Use” means to load and execute the object code version of the Software on any single computer to manage up to the number of Deployed Instances identified in the applicable Order Form, solely for the 
        internal business operations of End User and its Permitted Affiliates, as applicable.
        </p>
        
        <p>
        10.2.  Assignment. End User will not assign this EULA or its rights and obligations under this EULA to any third party without the prior written consent of rPath. For purposes of this Section 10.2, any change 
        of control of End User, whether by merger, sale of equity interests, or otherwise, will constitute an assignment requiring the prior written consent of rPath. Any attempt by End User to assign this EULA or its 
        rights and obligations hereunder in violation of this Section 10.2 will be null and void, and will constitute a material breach of this EULA.
        </p>
        
        <p>
        10.3.  Entire Agreement. This EULA supersedes all prior or contemporaneous agreements or representations including all non-disclosure or confidentiality agreements, whether written or oral, concerning the subject 
        matter hereof.  No addition to, or modification of, any provision of this EULA shall be binding upon the parties unless expressly stated to amend the terms hereof and approved by a duly authorized representative 
        of each party.  End User represents and acknowledges that in entering into this EULA it did not rely on any representations (whether innocent or negligent), warranties, or terms other than those expressly set 
        forth in this EULA.
        </p>
        
        <p>
        10.4.  Compliance with Laws. End User agrees at all times to comply with all laws and regulations applicable to its use of the Software and the Documentation and the performance of its obligations under this EULA.  
        Without limiting the generality of the foregoing, End User acknowledges that the license to use the Software hereunder is subject to the export control laws of the United States which may include, without limitation, 
        the United States Export Administration Regulations, the Trading With the Enemy Act, the International Emergency Economic Powers Act, the Arms Export Control Act and regulations promulgated by the United States 
        Department of the Treasury’s Office of Foreign Assets Control, as amended from time to time (collectively, the “Export Control Laws”).  End User agrees to comply with all applicable Export Control Laws.
        </p>
        
        <p>
        10.5.  Governing Law and Jurisdiction. This EULA is governed by the law of the State of North Carolina, USA (excluding the conflict of law rules of any jurisdiction or the United Nations Convention on Contracts for 
        the International Sale of Goods, the application of which is hereby expressly excluded).
        </p>
        
        <p>
        10.6.  Notices.  All notices and other communications given or made pursuant to this EULA concerning a breach, violation or termination hereof will be in writing and will be delivered: (i) by certified or registered 
        mail; or (ii) by an nationally recognized express courier. All notices or other communications to rPath shall be addressed to: rPath, Inc. 5430 Wade Park Blvd., Suite 310, Raleigh, NC 27607, USA, ATTENTION:  LEGAL 
        DEPARTMENT.  All notices to End User shall be sent to the address set forth in the Order Form.
        </p>
        
        <p>
        10.7.  Relationship between the Parties. rPath is an independent contractor.  Nothing in this EULA shall be construed to create an agency, joint venture, partnership, fiduciary relationship, joint venture or similar 
        relationship between the parties.
        </p>
        
        <p>
        10.8.  No Third Party Beneficiaries.  The warranties and obligations of rPath under this Agreement run only to End User, not to its Permitted Affiliates or Authorized Contractors, or any other persons.  Under no 
        circumstances shall any Affiliate of End User, Authorized Contractor, or any other person be considered a third party beneficiary of this Agreement or otherwise entitled to any rights or remedies under this 
        Agreement even if such Affiliates of End User, Authorized Contractor or other persons are provided access to the Software pursuant to this Agreement.
        </p>
        
        <p>
        10.9.  Severability. If any provision of this EULA is invalid or unenforceable, that provision shall be construed, limited, modified or, if necessary, severed to the extent necessary to eliminate its invalidity 
        or unenforceability, and the other provisions of this EULA shall remain in full force and effect.
        </p>
        
        <p>
        10.10.  Successors. All terms of this EULA shall be binding upon, inure to the benefit of, and be enforceable by and against the respective successors and permitted assigns of rPath and End User.
        </p>
        
        <p>
        10.11.  Waiver. No term of this EULA shall be deemed waived and no breach or default excused unless such waiver or excuse shall be in writing and signed by the party issuing the same. No action, regardless of form, 
        arising out of this EULA may be brought by End User more than one (1) year after the cause of action arose.
        </p>
        
        <p>
        10.12.  US Government Rights; Commercial Computer Software – Use Governed by Terms of Standard Commercial License. If the Software or Documentation is acquired by or on behalf of a unit or agency of the United States 
        Government, End User agrees that such Software or Documentation is “commercial computer software” or “commercial computer software” or “commercial computer software documentation” and that, absent a written agreement 
        to the contrary, the United States Government’s rights with respect to such Software or Documentation are limited by the terms specified in this EULA, pursuant to FAR 12.212(a) and/or DFARS 227.7202-1(a), as applicable.  
        The Software and Documentation have been developed exclusively at private expense, and have been available for license by members of the public.
        </p>

        <p>
        Copyright &#169; 2005 - 2012.  rPath, Inc.  All rights reserved.
        </p>
        
        <p>
        &quot;rPath,&quot; "rPath" Logo, "Powered by rPath" Logo, "rPath Lifecycle Management Platform" logo, "Conary,"  "rMake," "rBuilder," "rPath Cloud Engine," and "rPath Cloud Engine" Logo are trademarks and 
        service marks that are the property of rPath, Inc.
        </p> 

        <p>
        Revised May 15, 2012
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
