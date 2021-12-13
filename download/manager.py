import traceback
import os

from tqdm import tqdm

from download.sources.direct_source import DirectSource
from download.sources.spigotmc_source import SpigotmcSource
from download.sources.jenkins_source import JenkinsSource
from download.sources.github_source import GithubSource
from download.sources.papermc_source import PapermcSource

from download.post_processors.paperclip_post_processor import PaperclipPostProcessor
from download.post_processors.versionjson_post_processor import VersionjsonPostProcessor
from download.post_processors.plugin_post_processor import PluginPostProcessor
from download.post_processors.zip_post_processor import ZipPostProcessor

from download.destinations.basic_destination import BasicDestination
from download.destinations.s3_destination import S3Destination


class DownloadManager:
    direct_source = None
    spigotmc_source = None
    jenkins_source = None
    github_source = None
    papermc_source = None

    paperclip_post_processor = None
    plugin_post_processor = None
    zip_post_processor = None

    basic_destination = None
    s3_destination = None

    def __init__(self):
        self.direct_source = DirectSource()
        self.spigotmc_source = SpigotmcSource()
        self.jenkins_source = JenkinsSource()
        self.github_source = GithubSource()
        self.papermc_source = PapermcSource()

        self.paperclip_post_processor = PaperclipPostProcessor()
        self.versionjson_post_processor = VersionjsonPostProcessor()
        self.plugin_post_processor = PluginPostProcessor()
        self.zip_post_processor = ZipPostProcessor()

        self.basic_destination = BasicDestination()
        self.s3_destination = S3Destination()

    def download(self, source, name, url, post_processors, **kwargs):
        # Download file from the right source
        source = self.get_source_manager(source)
        downloaded_binary = source.download_element(url, **kwargs)

        # Run post_processors
        for post_processor in post_processors:
            processor = self.get_postprocessing_manager(post_processor)
            downloaded_binary, source, name, url = processor.process(
                downloaded_binary, source, name, url, **kwargs
            )

        # Save plugin somewhere
        destination = self.get_destination_manager()
        destination.save(downloaded_binary, source, name, url, **kwargs)

    def download_resources(self, resources):
        for resource in tqdm(resources, desc="Downloading resources"):
            try:
                self.download(**resource)
            except Exception:
                traceback.print_exc()

    def get_source_manager(self, source):
        return self.__getattr_safe("source", source)

    def get_postprocessing_manager(self, post_processor):
        return self.__getattr_safe("post_processor", post_processor)

    def get_destination_manager(self):
        destination = os.environ.get("DESTINATION", "basic")

        return self.__getattr_safe("destination", destination)

    def __getattr_safe(self, resource_name, value):
        # A simple wrapper to get our resources dynamically
        try:
            return getattr(self, "{}_{}".format(value, resource_name))
        except AttributeError:
            raise ValueError("{} {} is not supported".format(resource_name, value))
