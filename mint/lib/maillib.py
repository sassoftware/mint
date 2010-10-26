global _dnspython_present

try:
    import dns.resolver
    _dnspython_present = True
except ImportError:
    _dnspython_present = False

import smtplib
import socket
from email import MIMEText

from mint.mint_error import MailError

def digMX(hostname):
    try:
        answers = dns.resolver.query(hostname, 'MX')
    except dns.resolver.NoAnswer:
        return None
    return answers

def sendMailWithChecks(fromEmail, fromEmailName, toEmail, subject, body):
    validateEmailDomain(toEmail)
    try:
        sendMail(fromEmail, fromEmailName, toEmail, subject, body)
    except smtplib.SMTPRecipientsRefused:
        raise MailError("Email could not be sent: Recipient refused by server.")
    except socket.error, e:
        raise MailError("Email could not be sent: %s" % str(e))


def validateEmailDomain(toEmail):
    toDomain = smtplib.quoteaddr(toEmail).split('@')[-1][0:-1]
    VALIDATED_DOMAINS = ('localhost', 'localhost.localdomain')
    # basically if we don't implicitly know this domain,
    # and we can't look up the DNS entry of the MX
    # use gethostbyname to validate the email address
    try:
        if not ((toDomain in VALIDATED_DOMAINS) or digMX(toDomain)):
            socket.gethostbyname(toDomain)
    except (socket.gaierror, dns.resolver.NXDOMAIN):
        raise MailError("Email could not be sent: Bad domain name.")


def sendMail(fromEmail, fromEmailName, toEmail, subject, body):
    """
    @param fromEmail: email address for the From: header
    @type fromEmail: str
    @param fromEmailName: name for the From: header
    @type fromEmailName: str
    @param toEmail: recipient's email address
    @type toEmail: str
    @param subject: Email subject
    @type subject: str
    @param body: Email body text
    @type body: str
    """

    msg = MIMEText.MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = '"%s" <%s>' % (fromEmailName, fromEmail)
    msg['To'] = toEmail

    s = smtplib.SMTP()
    try:
        rAPA = xmlrpclib.ServerProxy('http://localhost:8004/xmlrpc/')
        config = rAPA.configure.Notify.index()
        s = smtplib.SMTP(host=config['mailRelay'])               
    except:
        # This simply means that we couldn't contact rAPA to get the relay,
        # and so we attempt to send mail directly
        pass

    s.connect()
    s.sendmail(fromEmail, [toEmail], msg.as_string())
    s.close()
