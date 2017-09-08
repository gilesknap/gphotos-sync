#!/usr/bin/python
# coding: utf8
import hashlib
import io
import mimetypes
import os.path


class LocalMedia(object):
    CHUNK_SIZE = 4096

    def __init__(self, media_path):
        self.path = media_path

    @property
    def filename(self):
        return os.path.basename(self.path)

    @property
    def canonical_filename(self):
        return self.filename

    @property
    def size(self):
        return os.path.getsize(self.path)

    @classmethod
    def read_chunk(cls, media_file):
        return media_file.read(LocalMedia.CHUNK_SIZE)

    @property
    def checksum(self):
        md5sum = hashlib.md5()
        with io.open(self.path, 'rb') as media_file:
            chunk_reader = self.read_chunk(media_file)
            for chunk in iter(chunk_reader, b""):
                md5sum.update(chunk)

        return md5sum.hexdigest()

    @property
    def mime_type(self):
        mime_type, _ = mimetypes.guess_type(self.path)
        return mime_type

