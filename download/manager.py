import traceback
import os

from tqdm import tqdm

from download.sources.spigotmc_source import SpigotMcSource
from download.sources.jenkins_source import JenkinsSource
from download.sources.github_source import GitHubSource

from download.postprocessors.plugin_postprocessor import PluginPostprocessor
from download.postprocessors.zip_postprocessor import ZipPostprocessor

from download.destinations.basic_destination import BasicDestination
from download.destinations.s3_destination import S3Destination


class DownloadManager():
    spigotmc_source = None
    jenkins_source = None
    github_source = None

    plugin_postprocessor = None
    zip_postprocessor = None

    basic_destination = None
    s3_destination = None

    def __init__(self):
        self.spigotmc_source = SpigotMcSource()
        self.jenkins_source = JenkinsSource()
        self.github_source = GitHubSource()

        self.plugin_postprocessor = PluginPostprocessor()
        self.zip_postprocessor = ZipPostprocessor()

        self.basic_destination = BasicDestination()
        self.s3_destination = S3Destination()

    def download(self, source, name, url, postprocessors, **kwargs):
        source = self.get_source_manager(source)
        downloaded_binary = source.download_element(url, **kwargs)

        for postprocessor in postprocessors:
            processor = self.get_postprocessing_manager(postprocessor)
            downloaded_binary, source, name, url = processor.process(downloaded_binary, source, name, url, **kwargs)

        destination = self.get_destination_manager()
        destination.save(downloaded_binary, source, name, url, **kwargs)

    def download_resources(self, resources):
        for resource in tqdm(resources):
            try:
                self.download(**resource)
            except:
                traceback.print_exc()

    def get_source_manager(self, source):
        return self.__getattr_safe('source', source)

    def get_postprocessing_manager(self, postprocessor):
        return self.__getattr_safe('postprocessor', postprocessor)

    def get_destination_manager(self):
        destination = os.environ.get('DESTINATION', 'basic')

        return self.__getattr_safe('destination', destination)

    def __getattr_safe(self, resource_name, value):
        try:
            return getattr(self, '{}_{}'.format(value, resource_name))
        except AttributeError:
            raise ValueError('{} {} is not supported'.format(resource_name, value))