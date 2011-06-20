from django.db import models
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import re
import inspect
import random

# ValidationErrors
PK_DOES_NOT_EXIST = r'Model (?P<model_name>([a-zA-Z]+|\s)+) with pk (?P<pk>\d+) does not exist.'
FIELD_ALREADY_EXISTS = r'(?P<model_name>([a-zA-Z]+|\s)+) with this (?P<field_name>([a-zA-Z]+|\s)+) already exists.'
FIELD_NAME_NOT_UNIQUE_FOR_DATE = r'(?P<field_name>([a-zA-Z]+|\s)+) must be unique for (?P<date_field>([a-zA-Z0-9]|[:]|\s)+) (?P<lookup>.*).'
FIELD_CANNOT_BE_NULL = r'This field cannot be null.'
FIELD_CANNOT_BE_BLANK = r'This field cannot be blank.'

class FzValidationError(ValidationError):
    ERRORS = {0:PK_DOES_NOT_EXIST,
              1:FIELD_ALREADY_EXISTS,
              2:FIELD_NAME_NOT_UNIQUE_FOR_DATE,
              3:FIELD_CANNOT_BE_NULL,
              4:FIELD_CANNOT_BE_BLANK,}
    
    def __init__(self, instance, e, *args, **kwargs):
        """
        message_dict = {'field_name1':[msg1, msg2, ...], field_name2:[...], ...}
        error_data = {'field_name1':[(code1, msg1, param_dict1), (code2, msg2, param_dict2)], ...}
        """
        ValidationError.__init__(self, 'Fuzzy Validation Failure', *args, **kwargs)
        self.instance = instance
        self.message_dict = e.message_dict
        self.error_data = self.resolveRegex()

    def resolveRegex(self):
        error_data = {}
        for fname, msgs in self.message_dict.items():
            error_data[fname] = []
            for msg in msgs:
                for code, error_regex in FzValidationError.ERRORS.items():
                    result = re.search(error_regex, msg)
                    if result:
                        param_dict = self.parseGroupDict(result)
                        err_tpl = (code, msg, param_dict)
                        error_data[fname].append(err_tpl)
        return error_data
        
    def parseGroupDict(self, result):
        gd = result.groupdict()
        if 'model_name' in gd:
            renamed = self.concatenateModelName(gd['model_name'])
            gd['model_name'] = renamed
        return gd

    def concatenateModelName(self, name):
        return ''.join([word.capitalize() for word in name]).split(' ')


# IntegrityErrors
COLUMN_IS_NOT_UNIQUE = r'column (?P<field_name>([a-zA-Z]+|\s)+) is not unique'
TABLE_ROWS_COLUMN_CANNOT_BE_NULL = r'(?P<table_name>[a-zA-Z0-9]+).(?P<column_name>[a-zA-Z0-9]+) may not be NULL'

class FzIntegrityError(IntegrityError):
    ERRORS = {0:COLUMN_IS_NOT_UNIQUE,
              1:TABLE_ROWS_COLUMN_CANNOT_BE_NULL,}
    
    def __init__(self, instance, e, *args, **kwargs):
        
        IntegrityError.__init__(self, e.args[0], *args, **kwargs)
        self.instance = instance
        self.message = e.args[0]
        info = self.resolveRegex()
        self.code, self.column = info
        
    def resolveRegex(self):
        for code, error_regex in FzIntegrityError.ERRORS.items():
            result = re.search(error_regex, self.message)
            if result:
                if code == 0:
                    return code, result.groupdict().get('field_name')
                elif code == 1:
                    return code, result.groupdict().get('column_name')
            else:
                import pdb; pdb.set_trace()


class FuzzyModel(object):

    def __init__(self, model, **kwargs):
        # if model is an instance of models.Model or FuzzyModel
        # then set self.models to model.__class__, else if model
        # is a class then set self.models to model
        if isinstance(model, (models.Model, FuzzyModel)):
            self.model = model.__class__
        else:
            assert inspect.isclass(model)
            self.model = model
        # if model is an instance of models.Model then set it as 
        # self.instance, else if model is 
        if isinstance(model, models.Model):
            self.instance = model
        elif isinstance(model, FuzzyModel):
            self.instance = model.instance
        else:
            self.instance = self.rand_get_or_create(**kwargs)

        self.fields = dict((f.name, f) for f in self.instance._meta.fields)
        self.related = dict((id(field), None) for field in self.FKFields.values())
    
    def rand_get_or_create(self, **kwargs):
        module = inspect.getmodule(self.model)
        mdlName = self.model.__name__
        try:
            # if similar model exists in db then get it
            qs_all = getattr(module, mdlName).objects.all()
            qs_filtered = qs_all.filter(**kwargs)
            instance = self.rand_instance_from_qs(qs_filtered)
        except Exception, e:
            instance = self.model()
        return instance

    def rand_instance_from_qs(self, qs):
        numResults = len(qs)
        if numResults:
            rng = range(0, numResults)
            return qs[random.choice(rng)]
        else:
            return self.model() if inspect.isclass(self.model) else self.model     

    def save(self):
        try:
            self.instance.clean_fields()
        except ValidationError, e:
            raise FzValidationError(self.instance, e)
        try:
            self.instance.validate_unique()
        except ValidationError, e:
            raise FzValidationError(self.instance, e)
        try:
            self.instance.save()
        except IntegrityError, e:
            raise FzIntegrityError(self.instance, e)
    
    @property
    def SimpleFields(self):
        fields = {}
        for fname, field in self.fields.items():
            if fname not in self.FKFields:
                fields[fname] = field
        return fields

    @property
    def FKFields(self):
        return dict((k, v) for k, v in self.fields.items() if isinstance(v, models.ForeignKey))

    @property
    def M2MFields(self):
        m2m_accessors = {}
        for m in self.instance._meta.get_m2m_with_model():
            f = m[0]
            try:
                m2m_accessors[f.name] = getattr(self.instance, f.name)
            except ValueError:
                pass
        return m2m_accessors

    def clean(self):
        try:
            self.instance.validate_unique()
        except ValidationError, e:
            raise FzValidationError(self.instance, e)
        try:
            self.instance.clean_fields()
        except ValidationError, e:
            raise FzValidationError(self.instance, e)


class FuzzyGraph(set):

    def __init__(self):
        set.__init__(self)
        self.registry = {}

    def add(self, fz, hsh=None):
        hsh = hsh if hsh else id(fz.instance.__class__)
        if hsh not in self:
            set.add(self, hsh)
            if hsh not in self.registry:
                self.registry[hsh] = fz

    def iterAdd(self, itr):
        for elm in itr:
            self.add(elm)

    def get(self, hsh, default=None):
        return self.registry.get(hsh, default)

    def remove(self, hsh):
        set.remove(self, hsh)
        del self.registry[hsh]

    def pop(self):
        hsh = set.pop(self)
        del self.registry[hsh]
        return hsh

    @classmethod
    def fromRegistry(cls, registry):
        fzG = cls()
        fzG.iterAdd(registry.values())
        return fzG

    @staticmethod
    def syncRegistry(fzG):
        hashes = fzG.registry.keys()
        for hsh in hashes:
            if hsh not in fzG:
                del fzG.registry[hsh]

    def _syncRegistry(self):
        FuzzyGraph.syncRegistry(self)

    @staticmethod
    def syncAgainst(S, fzG):
        for hsh in S:
            if hsh in fzG:
                continue
            else:
                del fzG.registry[hsh]

    def _syncAgainst(self, fzG):
        FuzzyGraph.syncAgainst(self, fzG)

    def union(self, fzG):
        un = set.union(self, fzG)
        fzs1 = dict((hsh, self.registry[hsh]) for hsh in self)
        fzs2 = dict((hsh, fzG.regsitry[hsh]) for hsh in fzG)
        
        
        dict_union = {}
        dict_union.update
        union = FuzzyGraph()
        return un
    
    def intersection(self, fzG):
        fzG_intersection = FuzzyGraph()
        inter = set.intersection(self, fzG)
        FuzzyGraph.syncRegistry(inter)
        return inter
    
    def difference(self, fzG):
        fzG_difference = FuzzyGraph()
        diff = set.difference(self, fzG)
        FuzzyGraph.syncRegistry(diff)
        return diff
    
    def symmetric_difference(self, fzG):
        sym_diff = set.symmetric_difference(self, fzG)
        FuzzyGraph.syncRegistry(sym_diff)
        return sym_diff

    def update(self, fzG):
        set.update(self, fzG)
        self.registry.update(fzG.registry)
        self._syncRegistry()


# class FuzzyDigraph(FuzzyGraph):
#     def __init__(self, fz):
#         FuzzyGraph.__init__(self)
#         self.populate(fz)
# 
#     def populate(self, fz):
#         for field in fz.FKFields.values():
#             parent = field.related.parent_model
#             fz_parent = FuzzyModel(parent)
#             if (id(fz.model), id(fz_parent.model)) in self:
#                 continue
#             else:
#                 self.add(fz, fz_parent)
#                 fz_parent_graph = FuzzyDigraph.__new__(self.__class__, fz_parent)
#                 self.union(fz_parent_graph)
#                 import pdb; pdb.set_trace()
# 
#     def add(self, fz1, fz2):
#         hsh1 = id(fz1.instance.__class__)
#         hsh2 = id(fz2.instance.__class__)
#         hsh = (hsh1, hsh2)
#         if hsh not in self:
#             set.add(self, hsh)
#             if hsh not in self.registry:
#                 self.registry[hsh] = (fz1, fz2)


class Fuzzer(object):

    GRAPH = FuzzyGraph()
    INTEGERS = range(0, 1000)
    STRINGS = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
    WORDS = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']

    def __init__(self, model, G=None, skip=None, force=None, fz_params=None, simple_only=False):
        self.fz_params = fz_params if fz_params else {}
        self.fz = model if isinstance(model, FuzzyModel) else FuzzyModel(model, **self.fz_params)
        self.fzG = G if isinstance(G, FuzzyGraph) else FuzzyGraph()
        self.fzG.add(self.fz)
        self.skipped = skip if skip else []
        self.forced = force if force else {}
        self.simple_only = simple_only
        self.DONE = []

        Fuzzer.GRAPH.update(self.fzG)

        for fname, field in self.fz.SimpleFields.items():
            if fname in self.forced:
                setattr(self.fz.instance, fname, self.forced[fname])
                continue
            if id(field) in [id(f) for f in self.skipped]:
                continue

            x = self.fuzzSimpleData(field)
            setattr(self.fz.instance, fname, x)
            self.DONE.append((fname, field))

        if not simple_only:
            for fname, fk in self.fz.FKFields.items():
                if fname in self.forced:
                    setattr(self.fz.instance, fname, self.forced[fname])
                    continue
                if id(fk) in [id(f) for f in self.skipped]:
                    continue

                self.fuzzFK(fk)
                self.DONE.append((fname, fk))

            for fname, accessor in self.fz.M2MFields.items():
                if fname in self.forced:
                    setattr(self.fz.instance, fname, self.forced[fname])
                    continue
                if id(accessor) in [id(f) for f in self.skipped]:
                    continue

                self.fuzzM2M(accessor)
                self.DONE.append((fname, accessor))

        self.save()

    @staticmethod
    def fuzzSimpleData(field):
        if isinstance(field, models.AutoField):
            x = Fuzzer.fuzzAutoField()
        elif isinstance(field, models.CharField):
            x = Fuzzer.fuzzCharField()
        elif isinstance(field, models.IntegerField):
            x = Fuzzer.fuzzIntegerField()
        elif isinstance(field, models.TextField):
            x = Fuzzer.fuzzTextField()
        elif isinstance(field, models.BooleanField):
            x = Fuzzer.fuzzBooleanField()
        elif isinstance(field, models.DecimalField):
            x = Fuzzer.fuzzDecimalField()
        else:
            return
        return x

    @staticmethod
    def fuzzDecimalField():
        return random.choice(Fuzzer.INTEGERS)

    @staticmethod
    def fuzzAutoField():
        return random.choice(Fuzzer.INTEGERS)

    @staticmethod
    def fuzzCharField():
        return random.choice(Fuzzer.STRINGS)

    @staticmethod
    def fuzzIntegerField():
        return random.choice(Fuzzer.INTEGERS)

    @staticmethod
    def fuzzTextField():
        return random.choice(Fuzzer.WORDS)

    @staticmethod
    def fuzzBooleanField():
        return random.choice([True, False])

    def fuzzFK(self, field):
        hsh = id(field.model)
        if hsh not in Fuzzer.GRAPH:
            Fuzzer.fuzzFzFK(self.fz, field)

    @staticmethod
    def fuzzFzFK(fz, field):
        parent = field.related.parent_model
        parent_hsh = id(parent)
        if parent_hsh in Fuzzer.GRAPH:
            result = Fuzzer.GRAPH.get(parent_hsh)
            if not result:
                import pdb; pdb.set_trace()
            assert len(result) == 1, 'len(result) > 1, result == %s' % result
            setattr(fz.instance, field.name, result[0].instance)
        else:
            parent_fz = Fuzzer(parent).fz
            setattr(fz.instance, field.name, parent_fz.instance)
        # Fuzzer.saveFz(fz)

    def fuzzM2M(self, field):
        hsh = id(field.model)
        if hsh not in Fuzzer.GRAPH:
            Fuzzer.fuzzFzM2M(self.fz, field)

    @staticmethod
    def fuzzFzM2M(fz, field):
        if hasattr(field, 'through'):
            related = {}
            through = field.through
            through_fields = dict((f.name, f) for f in through._meta.fields)
            for tFname, tField in through_fields.items():
                if hasattr(tField, 'rel'):
                    if hasattr(tField.rel, 'to'):
                        related[tFname] = tField.rel.to

            data = {}

            for rFname, rField in related.items():
                if isinstance(fz.instance, rField):
                    data[rFname] = fz.instance
                elif issubclass(field.model, rField):
                    rHsh = id(field.model)
                    if rHsh in Fuzzer.GRAPH:
                        data[rFname] = Fuzzer.GRAPH.get(rHsh)
                    else:
                        data[rFname] = Fuzzer(field.model).fz.instance

            for val in data.values():
                assert not isinstance(val, list)
                Fuzzer.saveFz(FuzzyModel(val))

            t = field.through(**data)
            Fuzzer.saveFz(FuzzyModel(t))
            
        else:
            import pdb; pdb.set_trace()

    def save(self):
        Fuzzer.saveFz(self.fz)

    @staticmethod
    def saveFz(fz):
        
        def reset(fname):
            bad = fz.fields[fname]
            if not bad:
                raise ValidationError
            if fname in fz.SimpleFields:
                x = Fuzzer.fuzzSimpleData(bad)
                setattr(fz.instance, fname, x)
            elif fname in fz.FKFields:
                Fuzzer.fuzzFzFK(fz, bad)
            elif fname in fz.M2MFields:
                Fuzzer.fuzzFzM2M(fz, bad)
            else:
                import pdb; pdb.set_trace()

        def resolveErrors(e):
            for fname, errors in e.error_data.items():
                for code, msg, params in errors:
                    if code == 0:
                        pk = int(params['pk'])
                        setattr(fz.instance, 'pk', pk)
                    elif code == 1:
                        reset(fname)
                    elif code == 2:
                        pass
                    elif code in (3, 4):
                        reset(fname)

        try:
            fz.clean()
        except FzValidationError, e:
            resolveErrors(e)
            try:
                fz.clean()
            except FzValidationError, e:
                resolveErrors(e)
                import pdb; pdb.set_trace()
        fz.save()

    @staticmethod
    def reset():
        Fuzzer.GRAPH = FuzzyGraph()