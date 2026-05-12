import logging
import threading
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
            # Serialize instantiation so concurrent download tasks (running in
            # threads via asyncio.to_thread) don't create duplicate singletons.
            self._lock = threading.Lock()

        def __getitem__(self, item):
            with self._lock:
                if item in self.obj_dict:
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
            "fabricmc": sources.FabricmcSource,
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
            "fabricmc": post_processors.FabricmcPostProcessor,
        }
    )

    DESTINATION_DICT = LazyLoader(
        {
            "basic": destinations.BasicDestination,
            "s3": destinations.S3Destination,
        }
    )

    @classmethod
    async def download(self, source, name, url, post_processors, max_tries=5, **kwargs):
        self.logger.info("Starting download of {} (source={}) from {}".format(name, source, url))
        tries = 0
        while True:
            try:
                # Download file from the right source. Source instantiation may
                # perform blocking I/O (e.g. SpigotMC login via FlareSolverr), so
                # run it on a thread to avoid stalling the event loop.
                source_manager = await asyncio.to_thread(self.get_source_manager, source)
                downloaded_binary = await source_manager.download_element(url, **kwargs)

                if not downloaded_binary:
                    raise ValueError(
                        "Downloaded empty binary for {} from {}".format(name, url)
                    )

                # Run post_processors
                for post_processor in post_processors:
                    processor = self.get_postprocessing_manager(post_processor)
                    downloaded_binary, source_manager, name, url = processor.process(
                        downloaded_binary, source_manager, name, url, **kwargs
                    )

                # Save plugin somewhere
                destination = self.get_destination_manager()
                destination.save(downloaded_binary, source_manager, name, url, **kwargs)
                self.logger.info("Downloaded {} from {}".format(name, url))
                break
            except Exception as exc:
                tries += 1
                if tries >= max_tries:
                    self.logger.error(
                        "Giving up on {} from {} after {} attempts (post_processors={}): {}: {}".format(
                            name, url, tries, post_processors, type(exc).__name__, exc
                        )
                    )
                    self.logger.error(traceback.format_exc())
                    break
                else:
                    self.logger.warning(
                        "Attempt {}/{} failed for {} from {}: {}: {} - retrying in {}s".format(
                            tries, max_tries, name, url, type(exc).__name__, exc, 5 * tries
                        )
                    )
                    await asyncio.sleep(5 * tries)

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
