<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->


    <?python
        for var in ['username', 'email', 'email2', 'fullName', 'displayEmail', 'blurb', 'tos', 'privacy']:
            kwargs[var] = kwargs.get(var, '')
    ?>
    <head>
        <title>${formatTitle('Create an Account')}</title>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${stepsWidget(['Get Started', 'Sign Up', 'Confirm Email'], 1)}
            </div>
            <div id="spanleft">
                <h2>Create an Account</h2>
                <p>
                    <span py:if="cfg.rBuilderOnline or cfg.tosLink">Please read the
                        <a href="${cfg.tosLink}" title="Terms of Service">Terms of Service</a>
                        before you create a new ${cfg.productName} account.</span>
                 Once you have completed the
                 form below, click <tt>Create</tt> and you will receive a
                 confirmation email containing a link required to complete
                 creation of your account.
                </p>
                <form method="post" action="processRegister">

                    <h3>Your ${cfg.productName} Account</h3>

                    <p>The information provided below will be used to
                    create your ${cfg.productName} account.</p>

                    <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Username:</em></th>
                            <td>
                                <input type="text" autocomplete="off" name="newUsername" maxlength="16" value="${kwargs['username']}"/>
                                 <p class="help">Please limit to 16 characters</p>
                            </td>
                        </tr>
                        <tr>
                            <th><em class="required">New Password:</em></th>
                            <td>
                                <input type="password" autocomplete="off" name="password" value="" />
                                <p class="help">Must be at least 6 characters</p>

                            </td>
                        </tr>
                        <tr>
                            <th><em class="required">Confirm Password:</em></th>
                            <td><input type="password" autocomplete="off" name="password2" value="" /></td>
                        </tr>
                        <tr>
                            <th><em class="required">Email Address:</em></th>
                            <td>
                                <input type="text" autocomplete="off" name="email" value="${kwargs['email']}"/>

                                <p class="help">A confirmation message will be sent to this address for verification
                                    You may need to enable email from ${cfg.adminMail} in your spam filtering software.
                                    You will not be able to access your account until you have confirmed your e-mail address.
                                </p>
                                <p py:if="cfg.rBuilderOnline or cfg.privacyPolicyLink" class="help">This email address will not be displayed on the ${cfg.productName} website
                                    and will never be shared or sold. More information can be found in our
                                    <a href="${cfg.privacyPolicyLink}" title="Privacy Policy">Privacy Policy</a>.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th><em class="required">Confirm Email:</em></th>
                            <td>
                                <input type="text" autocomplete="off" name="email2" value="${kwargs['email2']}"/>
                            </td>
                        </tr>
                    </table>
                    <h3>About You</h3>

                    <p>The information provided below will be displayed on your ${cfg.productName}
                    information page.  Use <tt>name at example dot com</tt> notation to make life more difficult for spammers.</p>

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th>Full Name:</th>
                            <td><input type="text" autocomplete="off" name="fullName" value="${kwargs['fullName']}" /></td>
                        </tr>
                        <tr>
                            <th>Contact Information:</th>
                            <td>
                                <textarea rows="3" type="text" name="displayEmail">${kwargs['displayEmail']}</textarea>

                                <p py:if="cfg.rBuilderOnline" class="help">Please enter alternate email addresses, web sites, IRC channels, IRC
                                nicks, and any other information that will help members of the ${cfg.productName} 
                                community contact you.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>About:</th>
                            <td>
                                <textarea rows="6" name="blurb">${kwargs['blurb']}</textarea><br/>

                                <p py:if="cfg.rBuilderOnline" class="help">Please enter a short
                                biography or any other relevant information
                                about yourself that you'd like to share
                                with the ${cfg.productName} community.</p>
                            </td>
                        </tr>
                    </table>


                    <p py:if="cfg.rBuilderOnline or cfg.tosLink"><input type="checkbox" class="check" name="tos" py:attrs="{'checked': kwargs['tos'] and 'checked' or None}"/> <em class="required">I have read and accept the <a href="${cfg.tosLink}" title="Terms of Service">Terms of Service</a></em></p>
                    <p py:if="cfg.rBuilderOnline or cfg.privacyPolicyLink"><input type="checkbox" class="check" name="privacy"  py:attrs="{'checked': kwargs['privacy'] and 'checked' or None}"/> <em class="required">I have read and accept the <a href="${cfg.privacyPolicyLink}" title="Privacy Policy">Privacy Policy</a></em></p>
                    <p><button id="createAccountSubmit" class="img" type="submit">
                        <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
                    </button></p>
                </form>
            </div>
        </div>
    </body>
</html>
