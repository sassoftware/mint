#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#


try:
    import boto
    import boto.s3
    import boto.s3.key
    from boto.exception import EC2ResponseError, S3ResponseError
    _boto_present = True
except ImportError:
    _boto_present = False

import xml.dom.minidom

from mint.db import ec2
from mint.lib import database
from mint.helperfuncs import urlSplit
from mint import mint_error
from rpath_common.xmllib import api1 as xmllib

class LaunchedAMI(database.TableObject):

    __slots__ = ec2.LaunchedAMIsTable.fields

    def getItem(self, id):
        return self.server.getLaunchedAMI(id)

    def save(self):
        return self.server.updateLaunchedAMI(self.launchedAMIId,
                self.getDataAsDict())

class BlessedAMI(database.TableObject):

    __slots__ = ec2.BlessedAMIsTable.fields

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
            
    def addError(self, code, message):
        """
        Add an error code and message
        @param code: a short error code description, such as "AuthError"
        @type  code: C{unicode}
        @param message: the error message
        @type  message: C{unicode}
        """
        doIt = True
        for error in self.errors:
            if error['message'].lower() == message.lower():
                doIt = False
                break
            
        if doIt:
            self.errors.append(dict(code=code, message=message))
                
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
            self.addError(ErrorResponseObject.unknownCode, 
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
            self.addError(code, message)
        
class S3Wrapper(object):

    __slots__ = ('s3conn', 'ec2conn', 'accountId', 'accessKey', 'secretKey')

    def __init__(self, (accountId, accessKey, secretKey), proxyUrl):
        
        # quick sanity check to prevent boto death
        if not accountId or not accessKey or not secretKey:
            errRespObj = ErrorResponseObject()
            errRespObj.addError(u'IncompleteCredentials', 
                                u'Incomplete set of credentials')
            raise mint_error.EC2Exception(errRespObj)    
        
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey
        pxArgs = S3Wrapper.splitProxyUrl(proxyUrl)
        self.s3conn = boto.connect_s3(self.accessKey, self.secretKey,
            **pxArgs)
        self.ec2conn = boto.connect_ec2(self.accessKey, self.secretKey,
            **pxArgs)

    def deleteAMI(self, amiId):
        """
        Deletes an ami id from Amazon S3.
        @param amiId: the ami id to delete.
        @type amiId: C{str}
        @return: the ami id deleted
        @rtype: C{str}
        """
        # Returns a one item list of the amiId we asked for.
        image = self.ec2conn.get_all_images(image_ids=amiId)

        # It's possible this image has already been deleted, handle that case
        # gracefully.
        if not image:
            raise mint_error.AMIInstanceDoesNotExist()
        image = image[0]

        # Image location should be of the format:
        # bucket-name/manifest-xml-file-name.xml
        manifest_path_bits = image.location.split('/')
        bucketName = manifest_path_bits[0]
        keyName = ''.join(manifest_path_bits[1:])

        bucket = self.s3conn.get_bucket(bucketName)
        key = boto.s3.key.Key(bucket, keyName)

        parts = []
        try:
            # Load the contents of the manifest, and read all the part
            # filenames and save them in parts.
            manifest_contents = key.get_contents_as_string()
            document = xml.dom.minidom.parseString(manifest_contents)
            parts = [x.firstChild.data \
                     for x in document.getElementsByTagName("filename")]

            # Delete each part.
            for part in parts:
                bucket.delete_key(part)

            # Delete the manifest.
            bucket.delete_key(keyName)
        except S3ResponseError:
            raise mint_error.EC2Exception(ErrorResponseObject(e))

        # Deregister the AMI, this removes the entry from AWS completely.
        self.ec2conn.deregister_image(amiId)

        return amiId

    @classmethod
    def splitProxyUrl(self, proxyUrl):
        if proxyUrl:
            splitUrl = urlSplit(proxyUrl)
        else:
            splitUrl = [ None ] * 7
        kwargs = {}
        kwargs['proxy_user'], kwargs['proxy_pass'], \
            kwargs['proxy'], kwargs['proxy_port'] = splitUrl[1:5]
        return kwargs

class EC2Wrapper(object):

    __slots__ = ('ec2conn', 'accountId', 'accessKey', 'secretKey')

    def __init__(self, (accountId, accessKey, secretKey), proxyUrl):
        
        # quick sanity check to prevent boto death
        if not accountId or not accessKey or not secretKey:
            errRespObj = ErrorResponseObject()
            errRespObj.addError(u'IncompleteCredentials', 
                                u'Incomplete set of credentials')
            raise mint_error.EC2Exception(errRespObj)    
        
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey
        pxArgs = S3Wrapper.splitProxyUrl(proxyUrl)
        self.ec2conn = boto.connect_ec2(str(self.accessKey), 
             str(self.secretKey), **pxArgs)

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
            raise mint_error.EC2Exception(ErrorResponseObject(e))

    def getInstanceStatus(self, ec2InstanceId):
        try:
            rs = self.ec2conn.get_all_instances(instance_ids=[ec2InstanceId])
            instance = rs[0].instances[0]
            return str(instance.state), str(instance.dns_name)
        except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))

    def terminateInstance(self, ec2InstanceId):
        try:
            self.ec2conn.terminate_instances(instance_ids=[ec2InstanceId])
            return True
        except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))
        
    def getAllKeyPairs(self, keyNames=None):
        try:
            keyPairs = []
            rs = self.ec2conn.get_all_key_pairs(keynames=keyNames)
            for pair in rs:
                keyPairs.append((str(pair.name), str(pair.fingerprint),
                                str(pair.material)))
            return keyPairs
        except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))
    
    def addLaunchPermission(self, ec2AMIId, awsAccountId):
        return self.addLaunchPermissions(ec2AMIId, [awsAccountId])

    def addLaunchPermissions(self, ec2AMIId, awsAccountIdList):
        try:
            self.ec2conn.modify_image_attribute(ec2AMIId, 'launchPermission',
                                                 'add',
                                                 user_ids=awsAccountIdList)
            return True
        except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))       

    def removeLaunchPermission(self, ec2AMIId, awsAccountId):
        return self.removeLaunchPermissions(ec2AMIId, [awsAccountId])

    def removeLaunchPermissions(self, ec2AMIId, awsAccountIdList):
        try:
            self.ec2conn.modify_image_attribute(ec2AMIId, 'launchPermission',
                                                 'remove',
                                                 user_ids=awsAccountIdList)
            return True
        except EC2ResponseError, e:
            # see if the error is because the ami no longer exists (ignore)
            error = e.errors and e.errors[0] or None
            if error and error["code"] == "InvalidAMIID.Unavailable":
                return True
            raise mint_error.EC2Exception(ErrorResponseObject(e))       

    def validateCredentials(self):
        self.getAllKeyPairs()
        return True

    def addPublicLaunchPermission(self, ec2AMIId):
         try:
            self.ec2conn.modify_image_attribute(ec2AMIId, 'launchPermission',
                                                'add', user_ids=None,
                                                groups=['all'] )
            return True
         except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))       
       
    def removePublicLaunchPermission(self, ec2AMIId):
         try:
            self.ec2conn.modify_image_attribute(ec2AMIId, 'launchPermission',
                                                'remove', user_ids=None,
                                                groups=['all'] )
            return True
         except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))       

    def resetLaunchPermissions(self, ec2AMIId):
         try:
            self.ec2conn.reset_image_attribute(ec2AMIId, 'launchPermission')
            return True
         except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))       

    def deregisterAMI(self, ec2AMIId):
        try:
            self.ec2conn.deregister_image(ec2AMIId)
            return True
        except EC2ResponseError, e:
            raise mint_error.EC2Exception(ErrorResponseObject(e))       
