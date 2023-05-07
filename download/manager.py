import logging
import traceback
import os

from tqdm import tqdm

from download.sources.direct_source import DirectSource
from download.sources.enginehub_source import EnginehubSource
from download.sources.spigotmc_source import SpigotmcSource
from download.sources.jenkins_source import JenkinsSource
from download.sources.modrinth_source import ModrinthSource
from download.sources.github_source import GithubSource
from download.sources.papermc_source import PapermcSource
from download.sources.zrips_source import ZripsSource

from download.post_processors.paperclip_post_processor import PaperclipPostProcessor
from download.post_processors.versionjson_post_processor import VersionjsonPostProcessor
from download.post_processors.plugin_post_processor import PluginPostProcessor
from download.post_processors.zip_post_processor import ZipPostProcessor

from download.destinations.basic_destination import BasicDestination
from download.destinations.s3_destination import S3Destination


class DownloadManager:
    logger = logging.getLogger("DownloadManager")

    class LazyLoader:
        class_dict: dict
        obj_dict: dict

        def __init__(self, class_dict):
            self.class_dict = class_dict
            self.obj_dict = {}

        def __getitem__(self, item):
            if item in self.obj_dict.keys():
                return self.obj_dict[item]

            obj = self.class_dict[item]()
            self.obj_dict[item] = obj
            return obj

    SOURCE_DICT = LazyLoader(
        {
            "direct": DirectSource,
            "enginehub": EnginehubSource,
            "spigotmc": SpigotmcSource,
            "jenkins": JenkinsSource,
            "modrinth": ModrinthSource,
            "github": GithubSource,
            "papermc": PapermcSource,
            "zrips": ZripsSource,
        }
    )

    POST_PROCESSOR_DICT = LazyLoader(
        {
            "paperclip": PaperclipPostProcessor,
            "versionjson": VersionjsonPostProcessor,
            "plugin": PluginPostProcessor,
            "zip": ZipPostProcessor,
        }
    )

    DESTINATION_DICT = LazyLoader(
        {
            "basic": BasicDestination,
            "s3": S3Destination,
        }
    )

    @classmethod
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

    @classmethod
    def download_resources(self, resources):
        for resource in tqdm(resources, desc="Downloading resources"):
            try:
                self.download(**resource)
            except Exception:
                self.logger.warning(
                    "Error while downloading {name} from {url} using source {source}".format(
                        **resource
                    )
                )
                traceback.print_exc()

    @classmethod
    def get_source_manager(self, source):
        return self.SOURCE_DICT[source]

    @classmethod
    def get_postprocessing_manager(self, post_processor):
        return self.POST_PROCESSOR_DICT[post_processor]

    @classmethod
    def get_destination_manager(self):
        destination = os.environ.get("DESTINATION", "basic")

        return self.DESTINATION_DICT[destination]
