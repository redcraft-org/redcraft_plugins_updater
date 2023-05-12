import logging
import traceback
import os
import asyncio

from download import sources
from download import post_processors
from download import destinations


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
            "direct": sources.DirectSource,
            "enginehub": sources.EnginehubSource,
            "spigotmc": sources.SpigotmcSource,
            "jenkins": sources.JenkinsSource,
            "modrinth": sources.ModrinthSource,
            "github": sources.GithubSource,
            "papermc": sources.PapermcSource,
            "zrips": sources.ZripsSource,
        }
    )

    POST_PROCESSOR_DICT = LazyLoader(
        {
            "paperclip": post_processors.PaperclipPostProcessor,
            "versionjson": post_processors.VersionjsonPostProcessor,
            "plugin": post_processors.PluginPostProcessor,
            "zip": post_processors.ZipPostProcessor,
            "fabricmod": post_processors.FabricmodPostProcessor,
            "quilt": post_processors.QuiltPostProcessor,
        }
    )

    DESTINATION_DICT = LazyLoader(
        {
            "basic": destinations.BasicDestination,
            "s3": destinations.S3Destination,
        }
    )

    @classmethod
    async def download(self, source, name, url, post_processors, **kwargs):
        try:
            # Download file from the right source
            source = self.get_source_manager(source)
            downloaded_binary = await source.download_element(url, **kwargs)

            if not downloaded_binary:
                raise ValueError("Downloaded empty binary for {} from {}".format(name, url))

            # Run post_processors
            for post_processor in post_processors:
                processor = self.get_postprocessing_manager(post_processor)
                downloaded_binary, source, name, url = processor.process(
                    downloaded_binary, source, name, url, **kwargs
                )

            # Save plugin somewhere
            destination = self.get_destination_manager()
            destination.save(downloaded_binary, source, name, url, **kwargs)
        except Exception:
            self.logger.error(
                "Error downloading {} from {} with post_processors {}".format(
                    name, url, post_processors
                )
            )
            self.logger.error(traceback.format_exc())

    @classmethod
    async def download_resources(self, resources):
        tasks = [self.download(**resource) for resource in resources]
        await asyncio.gather(*tasks)

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
