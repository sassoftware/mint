from xobj import xobj
from collections import deque

from mint.rest.modellib.ordereddict import OrderedDict

_converters = {}

def getConverterFactory(format):
    return _converters[format]

def fromText(format, inputText, outputClass, controller, request):
    factory = getConverterFactory(format)
    converter = factory.getConverter(outputClass)
    context = Context(controller, request)
    return converter.fromText(inputText, outputClass, context)

def toText(format, inputObject, controller, request):
    factory = getConverterFactory(format)
    converter = factory.getConverter(inputObject.__class__)
    context = Context(controller, request)
    return converter.toText(inputObject, context)

class Converter(object):

    def walkModelClass(self, model):
        for fieldName in model._fields:
            field = getattr(model, fieldName)
            if hasattr(field, 'displayName') and field.displayName:
                fieldName = field.displayName
            yield fieldName, field, field.getModel()


    def walkModelInstance(self, modelInstance, context):
        for fieldName in modelInstance._fields:
            field = getattr(modelInstance.__class__, fieldName)
            value = getattr(modelInstance, fieldName)
            if hasattr(field, 'displayName') and field.displayName:
                fieldName = field.displayName

            childModel = field.getModelInstance(value, modelInstance, context)
            if childModel is None:
                value = field.valueToString(value, modelInstance, context)
            yield fieldName, field, value, childModel

    def walkModelClassAndObject(self, modelClass, object, accessMethod=getattr):
        for fieldName in modelClass._fields:
            field = getattr(modelClass, fieldName)
            if hasattr(field, 'displayName') and field.displayName:
                attrName = field.displayName
            else:
                attrName = fieldName
            value = accessMethod(object, attrName, None)
            childModel = field.getModel()
            yield fieldName, field, value, childModel


class XobjConverterFactory(Converter):
    _xobjClassCache = {None : str}

    def getConverter(self, outputClass):
        if outputClass in self._xobjClassCache:
            # shortcut for the common case
            return XobjConverter(self._xobjClassCache[outputClass])
        attrs = {}
        entry = (outputClass, None, None, None, attrs)

        # toProcess is FIFO - deque is better.
        # toCreate is FILO - so use standard list.
        toProcess = deque([entry])
        toCreate =  [ entry ]

        while toProcess:
            # esentially a DFS the order in which to build xobj classes.
            # last to be found is the first to be converted into xobj.
            # likely we could avoid creating as long a toCreate list
            # if we didn't
            modelClass, field, attrName, parentDict, attrs = toProcess.popleft()
            for entry in self.walkModelClass(modelClass):
                name, field, childModel  = entry
                if childModel:
                    entry = (childModel, field, name, attrs, {})
                    if childModel not in self._xobjClassCache:
                        toProcess.append(entry)
                        # holder so we don't create twice while processing
                        # this same model.
                        self._xobjClassCache[childModel] = None
                    toCreate.append(entry)
                else:
                    toCreate.append((None, field, name, attrs, None))
                   
        while toCreate:
            modelClass, field, attrName, parentDict, attrs = toCreate.pop()
            xobjClass = self._xobjClassCache.get(modelClass, None)
            if not xobjClass:
                xobjClass = self.newXobjClass(modelClass, attrs)
                self._xobjClassCache[modelClass] = xobjClass
            if parentDict is not None:
                if field.isList():
                    parentDict[attrName] = [xobjClass]
                else:
                    parentDict[attrName] = xobjClass
            else:
                return XobjConverter(xobjClass)

    def newXobjClass(self, modelClass, attrs):
        attrs['__module__'] =  __name__
        attrs['_xobj'] = xobj.XObjMetadata(
            elements = modelClass._elements,
            attributes = OrderedDict.fromkeys(modelClass._attributes))
        className = modelClass._meta.name
        return type.__new__(type, className, xobj.XObj.__mro__, attrs)


class Context(object):
    def __init__(self, controller, request):
        self.controller = controller
        self.request = request
        
class XobjConverter(Converter):
    def __init__(self, xobjClass):
        self.xobjClass = xobjClass

    def getXobjObject(self, modelInstance, context):
        returnObject = self.xobjClass()
        origModelInstance = modelInstance
        toProcess = deque([ (returnObject, modelInstance) ])
        while toProcess:
            xobject, modelInstance = toProcess.popleft()
            xobjClass = xobject.__class__
            for entry in self.walkModelInstance(modelInstance, context):
                name, field, value, childModel = entry
                if not field.display:
                    continue
                if field.isText:
                    _xobj = xobject._xobj
                    xobject._xobj = xobj.XObjMetadata(
                        elements = _xobj.elements,
                        attributes = _xobj.attributes,
                        text=value)
                elif childModel is None:
                    setattr(xobject, name, value)
                elif field.isList():
                    childXobjClass = getattr(xobject.__class__, name)[0]
                    lst = []
                    setattr(xobject, name, lst)
                    for subModel in value:
                        childXobj = childXobjClass()
                        lst.append(childXobj)
                        toProcess.append((childXobj, subModel))
                else:
                    childXobj = getattr(xobject.__class__, name)()
                    setattr(xobject, name, childXobj)
                    toProcess.append((childXobj, childModel))
        return returnObject

    def fromXobjObject(self, xobjObject, modelClass, context):
        entry = (modelClass, xobjObject, {}, None, None)

        # toProcess is FILO
        toProcess = [(entry, False)]

        while toProcess:
            entry, finished = toProcess.pop()
            modelClass, xobject, attrs, parentDict, attrName = entry
            if not finished:
                toProcess.append((entry, True))
                for fieldData in self.walkModelClassAndObject(modelClass, 
                                                              xobject):
                    name, field, value, childModel = fieldData
                    if field.isList():
                        if value is None:
                            attrs[name] = None
                            continue
                        # Lists get automatically processed by their children,
                        # by appending to the value of parentDict (which is
                        # now a list :-/ )
                        # There is no need to finalize a list
                        lst = attrs[name] = []
                        # toProcess is FILO, so we need to push the first item
                        # in the list, last.
                        for lstValue in reversed(value):
                            # doesn't work for non-Model lists.
                            # List sub-entries do not get their own name, it
                            # is part of the child model
                            subEntry = (childModel, lstValue, {}, lst,
                                        None)
                            toProcess.append((subEntry, False))
                    elif childModel:
                        entry = (childModel, value, {}, attrs, name)
                        toProcess.append((entry, False))
                    else:
                        attrs[name] = field.valueFromString(value)
            else:
                if modelClass:
                    item = modelClass(**attrs)
                else:
                    item = field.valueFromString(xobject)
                if parentDict is not None:
                    if attrName is None:
                        # This is a sub-node of a list
                        parentDict.append(item)
                    else:
                        parentDict[attrName] = item
                elif not toProcess:
                    # queue is empty, return the results
                    return item

    def toText(self, modelInstance, context):
        xobjObject = self.getXobjObject(modelInstance, context)
        nsmap = getattr(modelInstance, 'nsmap', {})
        return xobj.toxml(xobjObject, xobjObject.__class__.__name__, nsmap=nsmap)

    def fromText(self, text, modelClass, context):
        className = self.xobjClass.__name__
        obj = xobj.parse(text, typeMap={className : self.xobjClass})
        xobjObject = getattr(obj, className)
        return self.fromXobjObject(xobjObject, modelClass, context)

_converters['xml'] = XobjConverterFactory()
