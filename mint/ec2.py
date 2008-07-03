#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

global _boto_present

try:
    import boto
    from boto.exception import EC2ResponseError
    _boto_present = True
except ImportError:
    _boto_present = False


from mint import database
from mint import mint_error
from mint.helperfuncs import toDatabaseTimestamp
from rpath_common.xmllib import api1 as xmllib

class BlessedAMIsTable(database.KeyedTable):
    name = 'BlessedAMIs'
    key = 'blessedAMIId'

    fields = ( 'blessedAMIId', 'ec2AMIId', 'buildId', 'shortDescription',
               'helptext', 'instanceTTL', 'mayExtendTTLBy',
               'isAvailable', 'userDataTemplate' )

    def getAvailable(self):
        cu = self.db.cursor()
        cu.execute("""SELECT blessedAMIId FROM BlessedAMIs
                      WHERE isAvailable = 1""")
        return [ x[0] for x in cu.fetchall() ]

class LaunchedAMIsTable(database.KeyedTable):
    name = 'LaunchedAMIs'
    key = 'launchedAMIId'

    fields = ( 'launchedAMIId', 'blessedAMIId', 'launchedFromIP',
               'ec2InstanceId', 'raaPassword', 'launchedAt',
               'expiresAfter', 'isActive', 'userData' )

    def getActive(self):
        cu = self.db.cursor()
        cu.execute("""SELECT launchedAMIId FROM LaunchedAMIs
                      WHERE isActive = 1""")
        return [ x[0] for x in cu.fetchall() ]

    def getCountForIP(self, ipaddr):
        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(launchedAMIId) FROM LaunchedAMIs
                      WHERE isActive = 1 AND launchedFromIP = ?""",
                      ipaddr)
        return cu.fetchone()[0]

    def getCandidatesForTermination(self):
        cu = self.db.cursor()
        cu.execute("""SELECT launchedAMIId, ec2InstanceId FROM LaunchedAMIs
                      WHERE isActive = 1 AND expiresAfter < ?""",
                      toDatabaseTimestamp())
        return [ x for x in cu.fetchall() ]

class LaunchedAMI(database.TableObject):

    __slots__ = LaunchedAMIsTable.fields

    def getItem(self, id):
        return self.server.getLaunchedAMI(id)

    def save(self):
        return self.server.updateLaunchedAMI(self.launchedAMIId,
                self.getDataAsDict())

class BlessedAMI(database.TableObject):

    __slots__ = BlessedAMIsTable.fields

    def getItem(self, id):
        return self.server.getBlessedAMI(id)

    def save(self):
        return self.server.updateBlessedAMI(self.blessedAMIId,
                self.getDataAsDict())
        
class ErrorResponseObject(xmllib.BaseNode):
    """
    A object that maps to the EC2 XML response error from boto.
    The data in this object consist of:
        errors: a list of errors in the form of [{code,message}, ...] extracted
                from the exception object XML
        requestId: a unicode string containing the original request ID extracted
                from the exception object XML
        status: the HTML status code extracted from the exception object
    """
    
    __slots__ = ('errors', 'requestId', 'status',)
    
    unknownCode = u'UnknownFailure'
    unknownMessage = u'An unknown failure occurred'
    
    def __init__(self, exceptionObj = None, attributes = None, nsMap = None, 
                 name = None):
        
        xmllib.BaseNode.__init__(self, attributes, nsMap, name)
        self.requestId = u''
        self.errors = []
        self.status = 0
        
        if exceptionObj:
            self.status = exceptionObj.status
            self.parseXML(exceptionObj.body)
                
    def addChild(self, childNode):
        """
        Override xmllib.BaseNode.addChild()
        """
        if childNode.getName() == 'RequestID':
            self.requestId = childNode.getText()
        if childNode.getName() == 'Errors':
            self._extractErrorNodeData(childNode.getChildren('Error'))
            
    def parseXML(self, xmlData):
        """
        Parse the response XML and set the proper values
        @param xmlData: the XML data to parse
        @type  xmlData: C{str}
        """
        if xmlData:
            binder = xmllib.DataBinder()
            binder.registerType(ErrorResponseObject, name = 'Response')
            binder.registerType(xmllib.StringNode, name = 'RequestId')
            obj = binder.parseString(xmlData)
            if obj and isinstance(obj, ErrorResponseObject):
                self.requestId = obj.requestId
                self.errors = obj.errors
                
        # there should always be error data present since this is an error obj
        if not self.errors:
            self._addError(ErrorResponseObject.unknownCode, 
                           ErrorResponseObject.unknownMessage)
            
    def freeze(self):
        """
        Marshal the object for transfer via XMLRPC
        @return: A tuple (status, requestId, errors)
        @rtype: C{tuple}
        """
        return self.status, self.requestId, self.errors
    
    def thaw(self, marshalledData):
        """
        Unmarshal the data
        @param marshalledData: The marshalled data
        """
        if marshalledData:
            self.status = marshalledData[0]
            self.requestId = marshalledData[1]
            self.errors = marshalledData[2]
    
    def _extractErrorNodeData(self, errorNodes):
        """
        Get the error data from the error nodes and update the objects values
        """
        for errorNode in errorNodes:
            code = ErrorResponseObject.unknownCode
            message = ErrorResponseObject.unknownMessage
            
            # handle the code nodes, should only be 1, but be safe since we
            # don't want to create an exception during error handling
            codeNodes = errorNode.getChildren('Code')
            if codeNodes and len(codeNodes) > 0:
                code = codeNodes[0].getText()
                
            # handle the message nodes, should only be 1, but be safe since we
            # don't want to create an exception during error handling
            messageNodes = errorNode.getChildren('Message')
            if messageNodes and len(messageNodes) > 0:
                message = messageNodes[0].getText()
                
            # add the error
            self._addError(code, message)
            
    def _addError(self, code, message):
        """
        Add an error and make sure error messages are not reported more than 
        once.  Error codes can be reported more than once.
        """
        doIt = True
        for error in self.errors:
            if error['message'].lower() == message.lower():
                doIt = False
                break
            
        if doIt:
            self.errors.append(dict(code=code, message=message))
        

class EC2Wrapper(object):

    __slots__ = ( 'ec2conn', 'accountId', 'accessKey', 'secretKey')

    def __init__(self, (accountId, accessKey, secretKey)):
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.ec2conn = boto.connect_ec2(self.accessKey, self.secretKey)

    def launchInstance(self, ec2AMIId, userData=None, useNATAddressing=False):

        # Get the appropriate addressing type to pass into the
        # Amazon API; 'public' uses NAT, 'direct' is bridged.
        # The latter method is deprecated and may go away in the
        # future.
        addressingType = useNATAddressing and 'public' or 'direct'
        try:
            ec2Reservation = self.ec2conn.run_instances(ec2AMIId,
                    user_data=userData, addressing_type=addressingType)
            ec2Instance = ec2Reservation.instances[0]
            return str(ec2Instance.id)
        except EC2ResponseError, e:
            raise EC2Exception(ErrorResponseObject(e))

    def getInstanceStatus(self, ec2InstanceId):
        try:
            rs = self.ec2conn.get_all_instances(instance_ids=[ec2InstanceId])
            instance = rs[0].instances[0]
            return str(instance.state), str(instance.dns_name)
        except EC2ResponseError, e:
            raise EC2Exception(ErrorResponseObject(e))

    def terminateInstance(self, ec2InstanceId):
        try:
            self.ec2conn.terminate_instances(instance_ids=[ec2InstanceId])
            return True
        except EC2ResponseError, e:
            raise EC2Exception(ErrorResponseObject(e))
        
    def getAllKeyPairs(self, keyNames=None):
        try:
            keyPairs = []
            rs = self.ec2conn.get_all_key_pairs(keynames=keyNames)
            for pair in rs:
                keyPairs.append((str(pair.name), str(pair.fingerprint),
                                str(pair.material)))
            return keyPairs
        except EC2ResponseError, e:
            raise EC2Exception(ErrorResponseObject(e))
    
    def validateCredentials(self):
        self.getAllKeyPairs()
        return True
