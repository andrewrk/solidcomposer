from .DummyStorage import DummyStorage, ensurePathExists, fileHash
from boto import s3

from django.conf import settings
import os

class S3Storage(DummyStorage):
    def __init__(self):
        self.connection = s3.Connection(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = self.connection.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

    def store(self, inFilename, file_id, reducedRedundancy=False):
        k = self.bucket.get_key(file_id)
        localHash = fileHash(inFilename)
        if k is not None:
            remoteHash = k.etag
            # sometimes remotehash is surrounded by quotes
            if len(remoteHash) == 34:
                remoteHash = remoteHash[1:-1]
            if remoteHash == localHash:
                # contents are identical
                return
        else:
            k = s3.Key(bucket=self.bucket, name=file_id)

        k.set_contents_from_filename(
            inFilename,
            policy='public-read',
            reduced_redundancy=reducedRedundancy
        )

    def retrieve(self, file_id, outFilename):
        k = self.bucket.get_key(file_id)
        assert k is not None
        # if file exists and hashes out the same, skip
        if os.path.exists(outFilename):
            localHash = fileHash(outFilename)
            remoteHash = k.etag
            # sometimes remotehash is surrounded by quotes
            if len(remoteHash) == 34:
                remoteHash = remoteHash[1:-1]
            if localHash == remoteHash:
                # contents are identical
                return

        ensurePathExists(outFilename)
        k.get_contents_to_filename(outFilename)

    def delete(self, file_id):
        k = self.bucket.get_key(file_id)
        if k is not None:
            k.delete()
