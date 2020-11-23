import os

from download.destinations.basic_destination import BasicDestination

class S3Destination(BasicDestination):

    s3_client = None

    def __init__(self):
        self.s3_client = None # TODO

    def save(self, downloaded_binary, source, name, url, **kwargs):
        pass # TODO
