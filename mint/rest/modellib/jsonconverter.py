#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import json

from mint.rest.modellib import converter

class JSONConverterFactory(converter.Converter):
    
    def getConverter(self, outputClass):
        return self

    def getDictFromModel(self, outputInstance, context):
        className = outputInstance._meta.name
        topLevel = {className : {}}
        toProcess = [(topLevel[className], outputInstance)]
        while toProcess:
            d, modelInstance = toProcess.pop()
            for entry in self.walkModelInstance(modelInstance, context):
                name, field, value, childModel = entry
                if value is None:
                    continue
                if childModel:
                    if field.isList():
                        d[name] = []
                        for childValue in value:
                            childDict = {}
                            d[name].append(childDict)
                            toProcess.append((childDict, childValue))
                    else:
                        d[name] = {}
                        toProcess.append((d[name], value))
                else:
                    d[name] = value
        return topLevel

    def getModelFromDict(self, jsonDict, modelClass, context):
        origModelClass = modelClass

        entry = (modelClass, jsonDict, {}, None, None)
        toProcess = [(entry, False)]
        while toProcess:
            entry, finished = toProcess.pop()
            modelClass, jsonDict, attrs, parentDict, attrName = entry
            if not finished:
                toProcess.append((entry, True))
                for fieldData in self.walkModelClassAndObject(modelClass, 
                                              jsonDict,
                                              accessMethod=dict.get):
                    name, field, value, childModel  = fieldData
                    if childModel:
                        entry = (childModel, value, {}, attrs, name)
                        toProcess.append((entry, False))
                    elif field.isList():
                        lst = []
                        entry = (None, lst, childAttrs, attrs, name)
                        toProcess.append((entry, True))
                        for lstValue in value:
                            # doesn't work for non-Model lists.
                            subEntry = (childModel, lstValue, childAttrs, lst, 
                                        None)
                            toProcess.append((subEntry, False))
                    else: 
                        attrs[name] = field.valueFromString(value)
            else:
                if modelClass:
                    item = modelClass(**attrs)
                else:
                    item = field.valueFromString(jsonDict)
                if parentDict is not None:
                    parentDict[attrName] = item
                elif modelClass is origModelClass:
                    return item

    def toText(self, modelInstance, context):
        d = self.getDictFromModel(modelInstance, context)
        return json.dumps(d)

    def fromText(self, text, modelClass, context):
        className = modelClass._meta.name
        d = json.loads(text)
        return self.getModelFromDict(d[className], modelClass, context)

        

converter._converters['json'] = JSONConverterFactory()
