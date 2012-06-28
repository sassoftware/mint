#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

import os
import hashlib
import json

class MultiRequestUploadHandler(object):
    def handle(self, uploaded_file, filename, chunk_id, num_chunks, checksum):
        if uploaded_file is None:
            raise Exception("No file uploaded")

        if chunk_id is None:
            chunk_id = 0
        chunk_id = int(chunk_id)

        if num_chunks is None:
            num_chunks = 1
        num_chunks = int(num_chunks)

        complete_file = filename
        incomplete_file = filename + '.incomplete'
        status_file = filename + '.status'

        if checksum is not None:
            md5_verify = hashlib.md5()
            for buf in uploaded_file.chunks():
                md5_verify.update(buf)

            if md5_verify.hexdigest() != checksum:
                raise Exception("Checksum error")

        # If this is the first chunk, start from clean slate
        if chunk_id == 0:
            try:
                os.remove(complete_file)
            except:
                pass
            try:
                os.remove(status_file)
            except:
                pass

            dir = os.path.dirname(filename)
            if not os.path.isdir(dir):
                os.makedirs(dir)

        # Append uploaded bytes to .incomplete file
        mode = 'wb' if chunk_id == 0 else 'ab'
        with open(incomplete_file, mode) as f:
            for buf in uploaded_file.chunks():
                f.write(buf)
        uploaded_file.close() # delete the tmp file

        # If this is the last chunk, finish up
        if chunk_id == num_chunks - 1:
            os.rename(incomplete_file, complete_file)
            try:
                os.remove(status_file)
            except:
                pass # it's not a big deal if we can't delete the status file
            current_file = complete_file

        else:
            status = {'status': 'uploading',
                      'chunk': chunk_id,
                      'chunks': num_chunks}

            with open(status_file, 'w') as f:
                json.dump(status, f)
            current_file = incomplete_file

        return MultiRequestUploadFile(current_file)

    def getStatus(self, filename):
        status = {'status': 'unknown'}
        if os.path.isfile(filename):
            status = {'status': 'finished'}
        elif os.path.isfile(filename + '.status'):
            with open(filename + '.status', 'r') as f:
                status = json.load(f)
        return status


class MultiRequestUploadFile(object):
    def __init__(self, filename):
        self.filename = filename

    def isComplete(self):
        return not self.filename.endswith('.incomplete')
