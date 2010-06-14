from .DummyStorage import DummyStorage, ensurePathExists
import settings

import os
import stat
import shutil

class LocalFileStorage(DummyStorage):
    def __init__(self):
        pass

    def store(self, inFilename, file_id, reducedRedundancy=False):
        full_out = os.path.join(settings.MEDIA_ROOT, file_id)
        ensurePathExists(full_out)
        shutil.copy2(inFilename, full_out)
        perms = stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH|stat.S_IWUSR|stat.S_IWGRP
        os.chmod(full_out, perms)

    def retrieve(self, file_id, outFilename):
        shutil.copy2(os.path.join(settings.MEDIA_ROOT, file_id), outFilename)

    def delete(self, file_id):
        os.remove(os.path.join(settings.MEDIA_ROOT, file_id))
