
class ErrorResponse(object):
    def processException(self, request, excClass, exception, tb):
        content = ['%s: %s\nTraceback:\n' % (excClass.__name__, exception)]
        content.append(''.join(traceback.format_tb(tb)))
        return Response(status=500, content=''.join(content), content_type='text/plain')

