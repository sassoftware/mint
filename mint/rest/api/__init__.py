def requires(modelName, model):
    def _requires(fn):
        fn.model = (modelName, model)
        return fn
    return _requires
